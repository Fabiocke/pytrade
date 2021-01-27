

from flask import Flask, make_response, request, render_template
import requests
from spyb3 import portfolio as pt
from spyb3.crawler import acoes
from bs4 import BeautifulSoup as bs

import zlib
import pickle

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

@app.route('/carteira/<params>')  # /landingpage/A
def carteira(params):
    import pandas as pd
    carteira = eval(f"pt.Carteira({params})")
    cstring=carteira.__repr__().replace('\n','<br>')
    df1=pd.DataFrame([['a', 1],['b', 4]],columns=['m', 'k'])
    return set_cookie('carteira',pickle.dumps(df1).replace(b'`',b'apostrofo'))


@app.route('/set_coockie/<v>_<r>')
def salvar(v,r):
    return f"<script>localStorage['{v}'] = '{r}'</script>"

def set_cookie(v,r):
    return f"""<html lang="pt-BR">
    <script>localStorage['{v}'] = `{r}`</script>"""



@app.route('/get_post_json/')
def get_post_json():    
    return  f"""<script>
                    document.write(myVar)
                    </script>"""
    data = request.get_json()

    return str(data)


@app.route('/geta/<f>')
def geta(f):    
    return cookie(f,0)


@app.route('/cookie/<s>_<g>')
def cookie(s,g):
    print(s,g)
    if not request.cookies.get(s):
        res = make_response()
        res.set_cookie(s,g)
    else:
        res = make_response(request.cookies.get(s))
    return res
    request.cache_control()


from flask_caching import Cache

@app.route('/setar/<v>_<r>')
def setar(v,r):
    cache.set(v,r)
    return ''

@app.route('/getar/<v>')
def getar(v):
    return str(cache.get(v))

#app.run()


