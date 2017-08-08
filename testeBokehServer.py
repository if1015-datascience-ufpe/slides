import pandas as pd
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

import bokeh.charts as charts
from bokeh.plotting import figure, show
from bokeh.io import output_notebook, push_notebook, curdoc
from bokeh.models import (Range1d, NumeralTickFormatter,
                          FixedTicker, Legend, DatetimeTickFormatter,
                          PreText, Select, Div, DataTable, NumberFormatter,
                          TableColumn)
from bokeh.palettes import Set1_7
from bokeh.layouts import gridplot, widgetbox

## Carregamento dos dados
x = ['../2017.1/data/ibge/ipca-reg-metropolitana-ago91_jul99.csv', \
'../2017.1/data/ibge/ipca-reg-metropolitana-jan12_jul16.csv', \
'../2017.1/data/ibge/ipca-reg-metropolitana-jul06_dez11.csv',\
 '../2017.1/data/ibge/ipca-reg-metropolitanas-ago99_jun06.csv']

ipca = pd.concat([pd.read_csv(a,index_col=[0,1],header=0,\
                                sep='\t',na_values=['nan','-'],\
                              decimal=',', ) for a in x], axis=1)

ipcalong = pd.melt(ipca.reset_index(),id_vars=['Regiao','OPCAO'],\
                        var_name='mes',value_name='ipca')

import locale
locale.setlocale(locale.LC_ALL, '')

## Preprocessamento
ipcalong.mes = pd.to_datetime(ipcalong.mes.str.title(),format='%b/%y')
ipcalong.ipca = ipcalong.ipca.values/100

from bokeh.models import ColumnDataSource

## Color mapping
corRegiao = dict(zip(ipcalong.Regiao.unique(),['#8dd3c7', '#ffffb3',
'#bebada', '#fb8072',
'#80b1d3', '#fdb462', '#b3de69', '#e41a1c',
'#377eb8', '#4daf4a', '#984ea3']))

## Transformacao de formato para adequar a Bokeh
df = pd.pivot_table(ipcalong,columns='Regiao',values='ipca',
                        index=['mes','OPCAO']).reset_index()

## Widget seletor de tipo/componente do IPCA
tipoIPCA = Select(title="Índice", value="Indice geral",
                    options=df.OPCAO.unique().tolist())
wbox = widgetbox([tipoIPCA],width=200)

## Bokeh data source (inicialmente com indice geral)
source=ColumnDataSource(df[df.OPCAO==tipoIPCA.value])

## Funcao de atualizacao da tabela com sumario dos dados
def media(attrname, old, new):
    selected = source.selected['1d']['indices']
    if selected:
        d = source.to_df()
        sumario.source = ColumnDataSource(d.iloc[selected, :].\
                                drop(['index','mes','OPCAO'],axis=1).describe().T.reset_index().\
                                rename(columns={'index':'Regiao'}))
    else:
        sumario.source = ColumnDataSource(source.to_df().drop(['index','mes','OPCAO'],axis=1).\
                                        describe().T.reset_index().rename(columns={'index':'Regiao'}))

## Definicao do callback para selecao de dados
source.on_change('selected',media)

## Funcao para atualizacao do grafico com base na escolha de um tipo de indice
def indice_update(attrname, old, new):
    source.data=ColumnDataSource(df[df.OPCAO==tipoIPCA.value]).data
    media(attrname,old,new)

## Definicao do callback no widget seletor de indice
tipoIPCA.on_change('value',indice_update)

## Encapsulamento da criacao da figura em uma funcao
def create_figure():
    p = figure(plot_height=400,plot_width=800,toolbar_location='above',
               tools="pan,box_select,tap,box_zoom,lasso_select,reset")

    p.xaxis.formatter = DatetimeTickFormatter(months='%b/%Y')
    p.yaxis.formatter = NumeralTickFormatter(format='0.00%')

    glyphs = {d : [p.circle('mes',d,source=source,
                            color=corRegiao[d], fill_alpha=0.3)]
              for d in ipcalong.Regiao.unique()}

    legend = Legend(items=list(glyphs.items()), location=(10, 120))
    legend.click_policy='hide'
    p.add_layout(legend,'right')
    return p


p = create_figure()

## Criacao da tabela com sumario dos dados
columns = [
        TableColumn(field="Regiao", title="Região"),
        TableColumn(field="mean", title="Média", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="min", title="Mínimo", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="max", title="Máximo", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="25%", title="1o Quartil", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="50%", title="Mediana", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="75%", title="3o Quartil", formatter=NumberFormatter(format='0.00%'))
]
sumario = DataTable(source=ColumnDataSource(source.to_df().drop(['index','mes','OPCAO'],
                                axis=1).describe().\
                                T.reset_index().\
                                rename(columns={'index':'Regiao'})),
                    columns=columns,
                    width=800)

## Adicionando layout ao documento
curdoc().add_root(gridplot([[wbox, p],[sumario]]))


## Tentativa de filtro por presidente/período
# presidentes = pd.read_csv('../2017.1/data/presidentes.csv',sep=';')
# presidentes.inicio = pd.to_datetime(presidentes.inicio,format='%d de %B de %Y')
# presidentes.fim = pd.to_datetime(presidentes.fim,format='%d de %B de %Y')
# presidentes.fim.fillna(ipcalong.mes.max(), inplace=True)
#
# corPartido = dict(zip(presidentes.partido.unique(),['teal','orange','blue','red']))
#
# boxes = presidentes.apply(lambda x: BoxAnnotation(left=x['inicio'].timestamp()*1000,\
#                                                        right=x['fim'].timestamp()*1000,\
#                                                        fill_color=corPartido[x['partido']],\
#                                                        fill_alpha=0.1), \
#                  axis=1).values
# boxes = dict(zip(presidentes.nome,boxes))
#
# periodo = Select(title="Presidente", value="Indice geral",
#                     options=df.OPCAO.unique().tolist())
