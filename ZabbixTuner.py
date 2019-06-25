#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__    = "Janssen dos Reis Lima"

from zabbix_api import ZabbixAPI
import os
import sys
import datetime
import time
import csv
from termcolor import colored
from progressbar import ProgressBar, Percentage, ReverseBar, ETA, Timer, RotatingMarker
from conf.zabbix import *

def banner():
    print colored('''
    ______       ______ ______ _____            ________
    ___  /______ ___  /____  /____(_)___  __    ___  __/___  _____________________
    __  / _  __ `/_  __ \_  __ \_  /__  |/_/    __  /  _  / / /_  __ \  _ \_  ___/
    _  /__/ /_/ /_  /_/ /  /_/ /  / __>  <      _  /   / /_/ /_  / / /  __/  /
    /____/\__,_/ /_.___//_.___//_/  /_/|_|      /_/    \__,_/ /_/ /_/\___//_/
    ''', 'red', attrs=['bold'])
    print "" 

try:
    zapi = ZabbixAPI(server=server, path="", timeout=timeout, log_level=loglevel)
    zapi.login(username, password)
except:
    os.system('clear')
    banner()
    print colored('    Não foi possível conectar ao Zabbix Server.', 'yellow', attrs=['bold'])
    print u"\n    Verifique se a URL " + colored(server, 'red', attrs=['bold']) + u" está disponível."
    print ""
    print colored('''
    Desenvolvido por Janssen Lima - janssenreislima@gmail.com
    ''', 'blue', attrs=['bold'])
    exit(0)

def menu():
    os.system('clear')
    banner()
    print colored("[+] - Bem-vindo ao ZABBIX TUNER - [+]\n"
    "[+] - Zabbix Tuner faz um diagnóstico do seu ambiente e propõe melhorias na busca de um melhor desempenho - [+]\n"
    "[+] - Desenvolvido por Janssen Lima - [+]\n"
    "[+] - Dúvidas/Sugestões envie e-mail para janssenreislima@gmail.com - [+]", 'blue')
    print ""
    print colored("--- Escolha uma opção do menu ---", 'yellow', attrs=['bold'])
    print ""
    print "[1] - Relatório de itens do sistema"
    print "[2] - Listar itens não suportados"
    print "[3] - Desabilitar itens não suportados"
    print "[4] - Iniciar diagnóstico"
    print "[5] - Relatório de Agentes Zabbix desatualizados"
    print "[6] - Relatório de Triggers por tempo de alarme e estado"
    print ""
    print "[0] - Sair"
    print ""
    menu_opcao()

def menu_opcao():
    opcao = raw_input("[+] - Selecione uma opção[0-7]: ")
    if opcao == '1':
        dadosItens()
    elif opcao == '2':
        listagemItensNaoSuportados()
    elif opcao == '3':
        desabilitaItensNaoSuportados()
    elif opcao == '4':
        diagnosticoAmbiente()
    elif opcao == '5':
        agentesDesatualizados()
    elif opcao == '6':
        menu_relack()
    elif opcao == '0':
        sys.exit()
    else:
        menu()

def desabilitaItensNaoSuportados():
    query = {
            "output": "extend",
            "filter": {
                "state": 1
            },
            "monitored": True
        }

    filtro = raw_input('Qual a busca para key_? [NULL = ENTER]')
    if filtro.__len__() > 0:
        query['search'] = {'key_': filtro}

    limite = raw_input('Qual o limite de itens? [NULL = ENTER]')
    if limite.__len__() > 0:
        try:
            query['limit'] = int(limite)
        except:
            print 'Limite invalido'
            raw_input("Pressione ENTER para voltar")
            main()

    opcao = raw_input("Confirma operação? [s/n]")
    if opcao == 's' or opcao == 'S':
        itens = zapi.item.get(query)
        print 'Encontramos {} itens'.format(itens.__len__())
        bar = ProgressBar(maxval=itens.__len__(), widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
        i = 0
        for x in itens:
            zapi.item.update({"itemid": x['itemid'], "status": 1})
            i += 1
            bar.update(i)
        bar.finish()
        print "Itens desabilitados!!!"
        print ""
        raw_input("Pressione ENTER para continuar")
    main()

def agentesDesatualizados():
    itens = zapi.item.get({
                            "filter": {"key_": "agent.version"},
                            "output": ["lastvalue", "hostid"],
                            "templated": False,
                            "selectHosts": ["host"],
                            "sortorder": "ASC"
    })
    
    try:
        versaoZabbixServer = zapi.item.get({
                                "filter": {"key_": "agent.version"},
                                "output": ["lastvalue", "hostid"],
                                "hostids": "10084"
                                })[0]["lastvalue"]
    
        print colored('{0:6} | {1:30}'.format("Versão", "Host"), attrs=['bold'])

        for x in itens:
            if x['lastvalue'] != versaoZabbixServer and x['lastvalue'] <= versaoZabbixServer:
                print '{0:6} | {1:30}'.format(x["lastvalue"], x["hosts"][0]["host"])
        print ""
        raw_input("Pressione ENTER para continuar")
        main()
    
    except IndexError:
        print "Não foi possível obter a versão do agent no Zabbix Server."
        raw_input("Pressione ENTER para continuar")
        main()
    
def diagnosticoAmbiente():
    print colored("[+++]", 'green'), "analisando itens não númericos"
    itensNaoNumericos = zapi.item.get({"output": "extend", "monitored": True,
        "filter": {"value_type": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]},
        "countOutput": True})
    print colored("[+++]", 'green'), "analisando itens ICMPPING com histórico acima de 7 dias"
    itensPing = zapi.item.get({"output": "extend", "monitored": True, "filter": {"key_": "icmpping"}})
    
    contPing = 0
    for x in itensPing:
        history = x["history"]
        if 'd' in history:
            dias = int(history.split('d')[0])
        if 'w' in history:
            dias = int(history.split('w')[0]) * 7
        if dias > 7:
            contPing += 1
    
    print ""
    print colored("Resultado do diagnóstico:", attrs=['bold'])
    print colored("[INFO]",
                  'blue'), "Quantidade de itens com chave icmpping armazenando histórico por mais de 7 dias:", contPing
    print colored("[WARN]", 'yellow', None,
                  attrs=['blink']), "Quantidade de itens não numéricos (ativos): ", itensNaoNumericos
    print ""
    raw_input("Pressione ENTER para continuar")
    main()
        
def listagemItensNaoSuportados():
    itensZabbix = {0: "Zabbix agent", 1: "SNMPv1", 2: "Zabbix trapper", 3: "Simple Check", 4: "SNMPv2",
        5: "Zabbix internal", 6: "SNMPv3", 7: "Zabbix agent(active)", 8: "Zabbix aggregate", 9: "web item",
        10: "external check", 11: "database monitor", 12: "IPMI agent", 13: "SSH agent", 14: "TELNET agent",
        15: "calculated", 16: "JMX agent", 17: "SNMP trap", 18: "Dependent item", 19: "HTTP agent",
                   }
    
    itensNaoSuportados = zapi.item.get(
        {"output": ["itemid", "error", "name", "type"], "filter": {"state": 1, "status": 0},
         "monitored": True, "selectHosts": ["hostid", "host"]})
    
    if itensNaoSuportados:
        print colored("\n[INFO]", 'green'), "Total de {} itens não suportados encontrados".format(
            itensNaoSuportados.__len__())
        opcao = raw_input("\nDeseja gerar relatorio em arquivo? [s/n]")
        if opcao == 's' or opcao == 'S':
            with open("relatorio_itens_nao_suportados.csv", "w") as arquivo:
                arquivo.write("Item,Tipo,Nome,Error,Host\r\n")
                for relatorio in itensNaoSuportados:
                    arquivo.write(relatorio["itemid"])
                    arquivo.write(",")
                    tipoItem = itensZabbix[int(relatorio["type"])]
                    arquivo.write(tipoItem)
                    arquivo.write(",")
                    arquivo.write(("\"" + relatorio["name"].replace('"', '') + "\"").encode('utf-8'))
                    arquivo.write(",")
                    arquivo.write(("\"" + relatorio["error"].replace('"', '') + "\"").encode('utf-8'))
                    arquivo.write(",")
                    arquivo.write(relatorio["hosts"][0]["host"])
                    arquivo.write("\r\n")
            
            raw_input("\nArquivo gerado com sucesso ! Pressione ENTER para voltar")
            main()
    else:
        print "Nenhum item 'não supotado' encontrado!!!"
        print ""
        raw_input("Pressione ENTER para continuar")
        main()

def dadosItens():
    itensNaoSuportados = zapi.item.get(
        {"output": "extend", "filter": {"state": 1, "status": 0}, "monitored": True, "countOutput": True})
    
    totalItensHabilitados = zapi.item.get(
        {"output": "extend", "filter": {"state": 0}, "monitored": True, "countOutput": True})
    
    itensDesabilitados = zapi.item.get(
        {"output": "extend", "filter": {"status": 1, "flags": 0}, "templated": False, "countOutput": True})
    
    """
    itensDescobertos = zapi.item.get({"output": "extend",
                                    "selectItemDiscovery": ["itemid"],
                                    "selectTriggers": ["description"],
                                    "monitored": True
                                    })
    """
    
    itensZabbixAgent = zapi.item.get(
        {"output": "extend", "filter": {"type": 0}, "templated": False, "countOutput": True, "monitored": True})
    
    itensSNMPv1 = zapi.item.get(
        {"output": "extend", "filter": {"type": 1}, "templated": False, "countOutput": True, "monitored": True})
    
    itensZabbixTrapper = zapi.item.get(
        {"output": "extend", "filter": {"type": 2}, "templated": False, "countOutput": True, "monitored": True})
    
    itensChecagemSimples = zapi.item.get(
        {"output": "extend", "filter": {"type": 3}, "templated": False, "countOutput": True, "monitored": True})
    
    itensSNMPv2 = zapi.item.get(
        {"output": "extend", "filter": {"type": 4}, "templated": False, "countOutput": True, "monitored": True})
    
    itensZabbixInterno = zapi.item.get(
        {"output": "extend", "filter": {"type": 5}, "templated": False, "countOutput": True, "monitored": True})
    
    itensSNMPv3 = zapi.item.get(
        {"output": "extend", "filter": {"type": 6}, "templated": False, "countOutput": True, "monitored": True})
    
    itensZabbixAgentAtivo = zapi.item.get(
        {"output": "extend", "filter": {"type": 7}, "templated": False, "countOutput": True, "monitored": True})
    
    itensZabbixAggregate = zapi.item.get(
        {"output": "extend", "filter": {"type": 8}, "templated": False, "countOutput": True, "monitored": True})
    
    itensWeb = zapi.item.get(
        {"output": "extend", "filter": {"type": 9}, "templated": False, "webitems": True, "countOutput": True,
         "monitored": True})
    
    itensExterno = zapi.item.get(
        {"output": "extend", "filter": {"type": 10}, "templated": False, "countOutput": True, "monitored": True})
    
    itensDatabase = zapi.item.get(
        {"output": "extend", "filter": {"type": 11}, "templated": False, "countOutput": True, "monitored": True})
    
    itensIPMI = zapi.item.get(
        {"output": "extend", "filter": {"type": 12}, "templated": False, "countOutput": True, "monitored": True})
    
    itensSSH = zapi.item.get(
        {"output": "extend", "filter": {"type": 13}, "templated": False, "countOutput": True, "monitored": True})
    
    itensTelnet = zapi.item.get(
        {"output": "extend", "filter": {"type": 14}, "templated": False, "countOutput": True, "monitored": True})
    
    itensCalculado = zapi.item.get(
        {"output": "extend", "filter": {"type": 15}, "templated": False, "countOutput": True, "monitored": True})
    
    itensJMX = zapi.item.get(
        {"output": "extend", "filter": {"type": 16}, "templated": False, "countOutput": True, "monitored": True})
    
    itensSNMPTrap = zapi.item.get(
        {"output": "extend", "filter": {"type": 17}, "templated": False, "countOutput": True, "monitored": True})
    
    itensDependentes = zapi.item.get(
        {"output": "extend", "filter": {"type": 18}, "templated": False, "countOutput": True, "monitored": True})
    
    itensHTTP = zapi.item.get(
        {"output": "extend", "filter": {"type": 19}, "templated": False, "countOutput": True, "monitored": True})
    print ""
    print "Relatório de itens"
    print "=" * 18
    print ""
    print colored("[INFO]", 'blue'), "Total de itens: ", int(totalItensHabilitados) + int(itensDesabilitados) + int(
        itensNaoSuportados)
    print colored("[INFO]", 'blue'), "Itens habilitados: ", totalItensHabilitados
    print colored("[INFO]", 'blue'), "Itens desabilitados: ", itensDesabilitados
    if itensNaoSuportados > "0":
        print colored("[ERRO]", 'red'), "Itens não suportados: ", itensNaoSuportados
    else:
        print colored("[-OK-]", 'green'), "Itens não suportados: ", itensNaoSuportados
    print ""
    print "Itens por tipo em monitoramento"
    print "=" * 31
    print colored("[INFO]", 'blue'), "Zabbix Agent (passivo): ", itensZabbixAgent
    print colored("[INFO]", 'blue'), "Zabbix Agent (ativo): ", itensZabbixAgentAtivo
    print colored("[INFO]", 'blue'), "Zabbix Trapper: ", itensZabbixTrapper
    print colored("[INFO]", 'blue'), "Zabbix Interno: ", itensZabbixInterno
    print colored("[INFO]", 'blue'), "Zabbix Agregado: ", itensZabbixAggregate
    print colored("[INFO]", 'blue'), "SNMPv1: ", itensSNMPv1
    print colored("[INFO]", 'blue'), "SNMPv2: ", itensSNMPv2
    print colored("[INFO]", 'blue'), "SNMPv3: ", itensSNMPv3
    print colored("[INFO]", 'blue'), "SNMNP Trap: ", itensSNMPTrap
    print colored("[INFO]", 'blue'), "JMX: ", itensJMX
    print colored("[INFO]", 'blue'), "IPMI: ", itensIPMI
    print colored("[INFO]", 'blue'), "SSH: ", itensSSH
    print colored("[INFO]", 'blue'), "Telnet: ", itensTelnet
    print colored("[INFO]", 'blue'), "Web: ", itensWeb
    print colored("[INFO]", 'blue'), "Checagem Simples: ", itensChecagemSimples
    print colored("[INFO]", 'blue'), "Calculado: ", itensCalculado
    print colored("[INFO]", 'blue'), "Checagem Externa: ", itensExterno
    print colored("[INFO]", 'blue'), "Database: ", itensDatabase
    print colored("[INFO]", 'blue'), "Itens dependentes: ", itensDependentes
    print colored("[INFO]", 'blue'), "HTTP: ", itensHTTP
    print ""
    raw_input("Pressione ENTER para continuar")
    main()

def menu_relack():
    os.system('clear')
    banner()
    print colored("[+] - Bem-vindo ao ZABBIX TUNER - [+]\n" 
    "[+] - Zabbix Tuner faz um diagnóstico do seu ambiente e propõe melhorias na busca de um melhor desempenho - [+]\n"
    "[+] - Desenvolvido por Janssen Lima - [+]\n"
    "[+] - Dúvidas/Sugestões envie e-mail para janssenreislima@gmail.com - [+]", 'blue')
    print ""
    print colored("--- Escolha uma opção para o relatório ---", 'yellow', attrs=['bold'])
    print ""
    print "[1] - Relatório de triggers com Acknowledged"
    print "[2] - Relatório de triggers com Unacknowledged"
    print "[3] - Relatório de triggers com ACK/UNACK"
    print ""
    print "[0] - Sair"
    print ""
    menu_opcao_relack()

def menu_opcao_relack():

    opcao = raw_input("[+] - Selecione uma opção[0-3]: ")

    params = {'output': ['triggerid', 'lastchange', 'comments', 'description'], 'selectHosts': ['hostid', 'host'], 'expandDescription': True, 'only_true': True, 'active': True}
    if opcao == '1':
        params['withAcknowledgedEvents'] = True
        label = 'ACK'
    elif opcao == '2':
        params['withUnacknowledgedEvents'] = True
        label = 'UNACK'
    elif opcao == '3':
        label = 'ACK/UNACK'
    elif opcao == '0':
        main()
    else:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()

    hoje = datetime.date.today()
    try:
        tmp_trigger = int(raw_input("[+] - Selecione qual o tempo de alarme (dias): "))
    except Exception, e:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()
    dt = (hoje - datetime.timedelta(days=tmp_trigger))
    conversao = int(time.mktime(dt.timetuple()))
    operador = raw_input( "[+] - Deseja ver Triggers com mais ou menos de {0} dias [ + / - ] ? ".format(tmp_trigger))

    if operador == '+':
        params['lastChangeTill'] = conversao
    elif operador == '-':
        params['lastChangeSince'] = conversao
    else:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()

    rel_ack = zapi.trigger.get(params)
    for relatorio in rel_ack:
        lastchangeConverted = datetime.datetime.fromtimestamp(float(relatorio["lastchange"])).strftime('%Y-%m-%d %H:%M')
        print ""
        print colored("[-PROBLEM-]", 'red'), "Trigger {} com {} de {} dias".format(label, operador, tmp_trigger)
        print "=" * 80
        print ""
        print colored("[INFO]", 'blue'), "Nome da Trigger: ", relatorio["description"], "| HOST:"+relatorio["hosts"][0]["host"]+" | ID:"+relatorio["hosts"][0]["hostid"]
        print colored("[INFO]", 'blue'), "Hora de alarme: ", lastchangeConverted
        print colored("[INFO]", 'blue'), "URL da trigger: {}/zabbix.php?action=problem.view&filter_set=1&filter_triggerids%5B%5D={}".format(server, relatorio["triggerid"])
        print colored("[INFO]", 'blue'), "Descrição da Trigger: ", relatorio["comments"]
        print ""

    print colored("\n[INFO]", 'green'), "Total de {} triggers encontradas".format(rel_ack.__len__())
    opcao = raw_input("\nDeseja gerar relatorio em arquivo? [s/n]")
    if opcao == 's' or opcao == 'S':
        with open("relatorio_triggers.csv", "w") as arquivo:
            arquivo.write("Nome da Trigger,Hora de alarme:,URL da trigger:,Descrição da Trigger:\r\n ")
            for relatorio in rel_ack:
                arquivo.write((relatorio["description"]).encode('utf-8'))
                arquivo.write(("| HOST:"+relatorio["hosts"][0]["host"]+" | ID:"+relatorio["hosts"][0]["hostid"]))
                arquivo.write(",")
                arquivo.write(lastchangeConverted)
                arquivo.write(",")
                arquivo.write("{}/zabbix.php?action=problem.view&filter_set=1&filter_triggerids%5B%5D={}".format(server, relatorio["triggerid"]))
                arquivo.write(",")
                arquivo.write(("\""+relatorio["comments"]+"\"").encode('utf-8'))
                arquivo.write("\r\n")

        raw_input("\nArquivo gerado com sucesso ! Pressione ENTER para voltar")
        menu_relack()
    else:   
        raw_input("\nPressione ENTER para voltar")
        menu_relack()


def main():
    menu()


main()
