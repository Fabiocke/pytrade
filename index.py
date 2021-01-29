

from flask import Flask, make_response, request, render_template
import requests
from spyb3 import portfolio as pt
from spyb3.crawler import acoes
from bs4 import BeautifulSoup as bs


app = Flask(__name__)

dictobjs={}

# Nome dos ativos no site do infomoney
def ativos_lista():
    r = requests.get('https://www.infomoney.com.br/cotacoes/empresas-b3/')
    s = bs(r.content, 'html.parser')
    a=s.findAll('tr')
    a=[[i.find('td', class_='higher'), i.findAll('td', class_='strong')] for i in a[1:]]
    a=[[i[0].text, [j.find('a').text.strip() for j in i[1]]]for i in a if any(i)]
    a=[[[ei, t] for ei in e] for t, e in zip([i[0] for i in a], [i[1] for i in a])]
    a=[j for i in a for j in i]
    return [i for i in a if (len(i[0])==5 and i[0][-1:] in ('3','4','5')) or (len(i[0])==6 and i[-2:]=='11')]
    

@app.route('/')
def home():
    set_obj()
    return render_template('index.html')

@app.route("/listaativos")
def listaativos():
    return str(ativos_lista())

@app.route("/get_my_ip")
def get_my_ip():
    return request.remote_addr

@app.route('/get_carteira/<params>', methods=['GET','POST'])  # /landingpage/A
def get_carteira(params):
    import pandas as pd
    ip = get_my_ip()
    
    if object_exist("dictobjs[ip]['carteira'][0]") and dictobjs[ip]['carteira'][0]==params:
        if request.method=='GET':
            return dictobjs[ip]['carteira'][1].__repr__().replace('\n','<br>')
        elif request.method=='POST':
            return dictobjs[ip]['carteira'][1]
    
    carteira = eval(f"pt.Carteira({params})")
    set_obj('carteira',[params, carteira])
    if request.method=='GET':
        return str(carteira.__repr__().replace('\n','<br>'))
    elif request.method=='POST':
        return carteira

@app.route('/carteira/<acao>')
def carteira(acao):
    ip=get_my_ip()
    return str(eval("dictobjs[ip]['carteira'][1]."+acao))


def object_exist(o):
    try:
        eval(o)
        return True
    except:
        return False

def set_obj(nm=0,v=0):
    ip = get_my_ip()
    if ip not in dictobjs:
        dictobjs.update({ip:{}})
    
    if nm and v:
        dictobjs[ip].update({nm:v})
    

app.run()


