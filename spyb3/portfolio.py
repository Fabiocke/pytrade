
import pandas as pd
from spyb3.crawler import acoes
#from scipy.stats import norm


def normal_cdf(x, mu=0,sigma=1):
    import math
    return (1 + math.erf((x - mu) / math.sqrt(2) / sigma)) / 2

def inverse_normal_cdf(p, mu=0, sigma=1, tolerance=0.00001):
    """encontra o inverso mais próximo usando a busca binária"""
    # se não for padrão, computa o padrão e redimensiona
    if mu != 0 or sigma != 1:
        return mu + sigma * inverse_normal_cdf(p, tolerance=tolerance)
    low_z, low_p = -10.0, 0 # normal_cdf(-10) está (muito perto de) 0
    hi_z, hi_p = 10.0, 1 # normal_cdf(10) está (muito perto de) 1
    while hi_z - low_z > tolerance:
        mid_z = (low_z + hi_z) / 2 # considera o ponto do meio e o valor da
        mid_p = normal_cdf(mid_z) # função de distribuição cumulativa lá
        if mid_p < p:
        # o ponto do meio ainda está baixo, procura acima
            low_z, low_p = mid_z, mid_p
        elif mid_p > p:
        # o ponto do meio ainda está alto, procura abaixo
            hi_z, hi_p = mid_z, mid_p
        else:
            break
    return mid_z


def Serie(ativo, volumes=[], intraday=0, periodo=[2010, 2030], dataini=0, dias = 0):
    ativo=[ativo]
    if dias:
        from datetime import datetime, timedelta
        periodo = [int((datetime.today() - timedelta(days=dias)).strftime('%Y%m%d')), int(datetime.today().strftime('%Y%m%d'))]
    return acoes.UolSeries().get(ativo, intraday, periodo, dataini)[0][0] if intraday else acoes.YahooSeries(ativo,periodo,dataini)[0][0]

# trabalha com um conjunto de series de ativos
class Carteira:
    def __init__(self, ativos, volumes=[], intraday=0, periodo=[2010, 2030], dataini=0, dias=0):
        ativos = ativos if type(ativos)==list else [ativos]
        if dias:
            from datetime import datetime, timedelta
            periodo = [int((datetime.today() - timedelta(days=dias)).strftime('%Y%m%d')), int(datetime.today().strftime('%Y%m%d'))]
        periodo = periodo if type(periodo)==list else [periodo]
        volumes = volumes if type(volumes)==list else [volumes]
        series = acoes.UolSeries().get(ativos, intraday, periodo, dataini) if intraday else acoes.YahooSeries(ativos,periodo,dataini)
        for i in series:
            setattr(self, i[1], i[0])
        setattr(self, 'ativos', ativos)
        self.add_volumes(volumes)
        
    def __getitem__(self, ativos):
        return getattr(self, ativos)
    
    def __repr__(self):
        if sum(self.volumes)>0:
            return '\n'.join([f'{a}: R$ {"%.2f" % v}' for a, v in zip(self.ativos, self.volumes)]) + f'\n\nTotal: R$ {"%.2f" % sum(self.volumes)}'
        else:
            return str(self.ativos)

    # Gera a coluna de retornos dia a  tipo = 0 gera o retorno por ln
    def gera_retornos(self, tipo=0):
        for i in self.ativos:
            self.__dict__[i] = self[i].gera_retornos(tipo)
        
    # Gera a coluna com médias móveis
    def medias_moveis(self, n):
        for i in self.ativos:
            self.__dict__[i] = self[i].media_movel(n)
            
    # insere volumes dos ativos da carteira
    # se o total for 0, a lista de volume será o valor total de cada ativo
    # se o total for definido, a lista de volumes serão as porcentagens
    def add_volumes(self, volumes, total=0):
        self.volumes = volumes if not total else [i/100*total for i in volumes]
            
    # matriz de correlação
    def matriz_correl(self):
        self.gera_retornos()
        m = [[self[j][['dataref', 'retornos']].merge(self[i][['dataref', 'retornos']], on='dataref') for j in self.ativos] for i in self.ativos]
        m = [[i[['retornos_x','retornos_y']].corr().values[0][1] for i in s] for s in m]
        return pd.DataFrame(m, columns=self.ativos, index = self.ativos)
    
    # Gera a porcentagem que cada ativo ocupa no portfolio que são os pesos
    def ponderar(self):
        total = sum(self.volumes)
        if total:
            return [v/total for v in self.volumes]

    # gera o beta da carteira
    def coefbeta(self):
        betas = [self[a].coefbeta() for a in self.ativos]
        return sum([i*j for i,j in zip(betas, self.ponderar())])

    # Gera o retorno médio dos ativos
    def retorno_ativos(self):
        return [self[a].gera_retornos().retornos.mean() for a in self.ativos]

    # soma os retornos médios ponderados para obter o retorno médio da carteira
    def retorno_carteira(self, aa=0):
        r = sum([m[0]*m[1] for m in zip(self.retorno_ativos(), self.ponderar())])
        return r if not aa else (1+r)**252-1
                  
    # Gera a volatilidade de cada ativo
    def std(self):
        return [self[i].std() for i in self.ativos]


    # Gera a volatilidade da carteira
    # fonte: http://ferramentasdoinvestidor.com.br/financas-quantitativas/matematica-de-portfolio/
    def vol_carteira(self, aa=0):
        # obtem a matriz de correlação
        matriz = self.matriz_correl().values.tolist()
        # vetor de pesos de cada ativo
        pesos = self.ponderar()    
        # vetor de desvios
        stds = self.std()
        # matriz de ativos       
        l = [sorted([n1,n2]) for n1, _ in enumerate(self.ativos) for n2,_ in enumerate(self.ativos) if n1!=n2]
        l = list(map(list, set(map(frozenset, l))))
        # calculo
        vol = sum([2*stds[n1]*stds[n2]*pesos[n1]*pesos[n2]*matriz[n1][n2] for n1, n2 in l]+[p**2*o**2 for p, o in zip(pesos, stds)])**(1/2)
        return vol if not aa else vol*(252**0.5)                     

    def coeficiente_variacao(self):
        return self.vol_carteira(aa=1)/self.retorno_carteira(aa=1)

    # calcula o value at risk da carteira para determinado nível de confiança em determinada quantidade de dias
    def risco(self, nc, dias=1):
        return self.vol_carteira()*inverse_normal_cdf(nc)*sum(self.volumes)*(dias**0.5)                              

    # obtem o risco país do Brasil
    def risco_pais(self):
        return

    # obtem a inflação no brasil ou eua:
    def inflacao(self, pais):
        return

    # obtem a taxa livre de risco
    def tx_livre_risco(self, pais):
        return

    # calcula o ke do ativo (rm=retorno esperado)
    def ke(self, rm):
        return self.tx_livre_risco()+self.coefbeta()*(rm-self.tx_livre_risco())




