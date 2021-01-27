

from flask import Flask, make_response, request, render_template
import requests
from bs4 import BeautifulSoup as bs

app = Flask(__name__)

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
    return render_template('index.html')

@app.route("/listaativos")
def listaativos():
    return str(ativos_lista())





