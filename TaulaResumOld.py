import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
from PyQt5.QtWidgets import QAction,QMessageBox,QTableWidgetItem, QApplication, QFileDialog,QToolBar

#from qgis.core import QgsDataSourceURI
from qgis.utils import iface
import psycopg2
from decimal import *
import unicodedata

# Initialize Qt resources from file resources.py
from resources import *

# Import the code for the dialog
from TaulaResum_dialog import TaulaResumDialog
import os.path


"""
Variables globals per a la connexio
"""
nomBD1=""
contra1=""
host1=""
port1=""
usuari1=""
schema=""
micolor=None
Versio_modul="V_Q3.210215"
cur = None
conn = None

'''
Classe principal 'Taula Resum'
'''
class TaulaResumOld:    
    def crearTaula(self):
        '''
        Funcio principal:
        Funcio creadora de les taules.
        1. Es connecta amb la BDD escollida
        2. Inicialitza variables per crear les instruccions SQL
        3. Transforma les instruccions donades per l'usuari en sentencies SQl.
        4. Tria quin dels metodes de treball s'utilitza i executa les sentencies.
        5. Graba el resultat a la BDD
        6. Treu un missatge on comptabilitza el nombre d'habitants que formen les taules.
        '''        
        global nomBD1
        global contra1
        global host1
        global port1
        global usuari1
        global schema
        s = QSettings()
        
        
        self.dlg.setEnabled(False)
        self.setProcessant()
        '''Control d'errors'''
        if ((not self.dlg.btoEDAT.isChecked()) and (not self.dlg.btoGENERE.isChecked()) and (not self.dlg.btoESTUDIS.isChecked()) and (not self.dlg.btoORIGEN.isChecked()) and (not self.dlg.btoNACIONALITAT.isChecked())):
                QMessageBox.information(None, "Error 1", "No hi ha cap filtre seleccionat.\nSeleccioneu un filtre.")
                self.dlg.setEnabled(True)
                self.tornaConnectat()
                #print ("No hi ha cap filtre seleccionat.\nSeleccioneu un filtre.")
        else:
            nom_conn=self.dlg.comboConnexions.currentText()
            select = 'Selecciona connexió'
            if (nom_conn != select):
                #fileName = QtGui.QFileDialog.getSaveFileName(self.dlg, "Guardar com...", "c:/", "CSV files (*.csv)")
                ##startingDir = cmds.workspace(q=True, rootDirectory=True)
                '''Eleccio del cami de destí dels arxius'''
                fileName= QFileDialog.getExistingDirectory(self.dlg,"Open a folder","c:/",QFileDialog.ShowDirsOnly)
                if fileName != '':
                                       
                    s.beginGroup("PostgreSQL/connections/"+nom_conn)
                    currentKeys = s.childKeys()
                    '''Connexio'''
                    nomBD1 = s.value("database", "" )
                    contra1 = s.value("password", "" )
                    host1 = s.value("host", "" )
                    port1 = s.value("port", "" )
                    usuari1 = s.value("username", "" )
                    
                    self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #ffff7f')
                    self.dlg.lblEstatConn.setText('Connectant...')
                    self.dlg.lblEstatConn.setAutoFillBackground(True)
                    QApplication.processEvents()
                    
                    #Sentencia SQL Estudis
                    where = 'where '      
                    
                    #Connexio
                    nomBD = nomBD1.encode('ascii','ignore')
                    usuari = usuari1.encode('ascii','ignore')
                    servidor = host1.encode('ascii','ignore')     
                    contrasenya = contra1.encode('ascii','ignore')
                    try:
                        estructura = "dbname='"+ nomBD.decode("utf-8") + "' user='" + usuari.decode("utf-8") +"' host='" + servidor.decode("utf-8") +"' password='" + contrasenya.decode("utf-8") + "'"# schema='"+schema+"'"
                        conn = psycopg2.connect(estructura)
                        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: rgb(255, 170, 142)')
                        self.dlg.lblEstatConn.setText('Connectat i processant')
                        QApplication.processEvents()
                        cur = conn.cursor()
                        
                        '''Composicio del where'''
                        '''Filtre d'edat'''
                        if self.dlg.btoEDAT.isChecked():
                            max = 0
                            min = 0
                            try:
                                max = int(self.dlg.txtEdatMax.text())
                                min = int(self.dlg.txtEdatMin.text())
                                
                            except Exception as ex:
                                print("Error al llegir les edats.\nEls camps edat mínima i edat màxima han d'estar plens")
                                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                message = template.format(type(ex).__name__, ex.args)
                                print (message)
                                QMessageBox.information(None, "Error", u"Error al llegir les edats.\nEls camps edat mínima i edat màxima han d'estar plens")
                                self.dlg.GrupPestanyes.setCurrentIndex(0)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                return
                            
                            if ((min > max) or (min < 0) or (max <= 0)):
                                QMessageBox.information(None, "Error", u"Error:\n minim > màxim o número/s negatiu/s")
                                self.dlg.GrupPestanyes.setCurrentIndex(0)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                return
                            hora = self.dlg.data.date()
                            horaAct = QtCore.QDateTime.currentDateTime()
                            diaActual = str(horaAct.date().day()) + "-" + str(horaAct.date().month()) + "-" + str(horaAct.date().year())
                            
                            if self.dlg.btoEdatRestrictiu.isChecked():
                                if self.dlg.btoData.isChecked():
                                    diaTriatMin = str(hora.day()) + "-" + str(hora.month()) + "-" + str(hora.year() - min)
                                    diaTriatMax = str(hora.day()) + "-" + str(hora.month()) + "-" + str(hora.year() - max)
                                    where += '"HABFECNAC" >= to_date(' + "'" + diaTriatMax + "'," + "'DD-MM-YYYY')" + ' AND "HABFECNAC" <= to_date(' + "'" + diaTriatMin + "'," + "'DD-MM-YYYY')"
                                    
                                elif self.dlg.btoDataAvui.isChecked():
                                    diaTriatMin = str(horaAct.date().day()) + "-" + str(horaAct.date().month()) + "-" + str(horaAct.date().year() - min)
                                    diaTriatMax = str(horaAct.date().day()) + "-" + str(horaAct.date().month()) + "-" + str(horaAct.date().year() - max)
                                    where += '"HABFECNAC" >= to_date(' + "'" + diaTriatMax + "'," + "'DD-MM-YYYY')" + ' AND "HABFECNAC" <= to_date(' + "'" + diaTriatMin + "'," + "'DD-MM-YYYY')"
                            elif self.dlg.btoEdatAmpli.isChecked():
                                if self.dlg.btoData.isChecked():
                                    diaTriatMin = str(hora.day()) + "-" + str(hora.month()) + "-" + str(hora.year() - min)
                                    diaTriatMax = str(hora.day()) + "-" + str(hora.month()) + "-" + str(hora.year() - (max+1))
                                    where += '"HABFECNAC" > to_date(' + "'" + diaTriatMax + "'," + "'DD-MM-YYYY')" + ' AND "HABFECNAC" <= to_date(' + "'" + diaTriatMin + "'," + "'DD-MM-YYYY')"
                                    
                                elif self.dlg.btoDataAvui.isChecked():
                                    diaTriatMin = str(horaAct.date().day()) + "-" + str(horaAct.date().month()) + "-" + str(horaAct.date().year() - min)
                                    diaTriatMax = str(horaAct.date().day()) + "-" + str(horaAct.date().month()) + "-" + str(horaAct.date().year() - (max+1))
                                    where += '"HABFECNAC" > to_date(' + "'" + diaTriatMax + "'," + "'DD-MM-YYYY')" + ' AND "HABFECNAC" <= to_date(' + "'" + diaTriatMin + "'," + "'DD-MM-YYYY')"
                        
                        '''Filtre de genere'''    
                        if self.dlg.btoGENERE.isChecked():
                            if self.dlg.btoEDAT.isChecked():
                                where += ' AND '
                            if self.dlg.btoHome.isChecked():
                                where += '"HABELSEXO" = 1'
                            elif self.dlg.btoDona.isChecked():
                                where += '"HABELSEXO" = 6'
                            else:
                                QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap gènere seleccionat.")
                                self.dlg.GrupPestanyes.setCurrentIndex(1)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                return
    
                        '''Filtre d'estudis'''
                        if self.dlg.btoESTUDIS.isChecked():
                            if self.dlg.btoEDAT.isChecked() or self.dlg.btoGENERE.isChecked():
                               where += ' AND '
                            llistaEST = self.dlg.llistaEstudis.selectedItems()
                            if len(llistaEST)>0:
                                for item in llistaEST:
                                    where += '"HABNIVINS" = '+ item.toolTip() + ' OR '
                                where=where[0:len(where)-4]
                            else:
                                QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap estudi seleccionat.")
                                self.dlg.GrupPestanyes.setCurrentIndex(2)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                return
                        
                        '''Filtre d'origen'''
                        if self.dlg.btoORIGEN.isChecked():
                            if self.dlg.btoEDAT.isChecked() or self.dlg.btoGENERE.isChecked() or self.dlg.btoESTUDIS.isChecked():
                               where += ' AND '
                            if self.dlg.btoPais.isChecked():
                                llistaORG = self.dlg.LlistaPais.selectedItems()
                                if len(llistaORG)>0:
                                    for item in llistaORG:
                                        if item.toolTip() != '108':
                                            where += '"HABCOMUNA" = '+ item.toolTip().replace("\'","''") + ' AND "HABCOPANA" != 108' + ' OR '
                                        else:
                                            where += '"HABCOPANA" = 108' + ' OR '
                                    where=where[0:len(where)-4]
                                else:
                                   QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap país seleccionat.")
                                   self.dlg.GrupPestanyes.setCurrentIndex(3)
                                   self.tornaConnectat()
                                   self.dlg.setEnabled(True)
                                   return 
                            elif self.dlg.btoZones.isChecked():
                                llistaORG = self.dlg.LlistaZonesCont.selectedItems()
                                if len(llistaORG)>0:
                                    zonaCont = 'WHERE '
                                    for item in llistaORG:
                                        zonaCont += '"CONZONCON" = '  + chr(39) + item.toolTip().replace("\'","''")  + chr(39) + ' OR '

                                    zonaCont=zonaCont[0:len(zonaCont)-4]
                                    SQL_Pro = 'SELECT "CONCODPAI" from "public"."CONTINENTS" '  + zonaCont  + ' ORDER BY 1'                                    
                                    
                                    try:
                                        cur.execute(SQL_Pro)
                                        rows = cur.fetchall()
                                    except Exception as ex:
                                        print("Error SELECT concodpai")
                                        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                        message = template.format(type(ex).__name__, ex.args)
                                        print (message)
                                        self.tornaConnectat()
                                        QMessageBox.information(None, "Error", "Error SELECT concodpai")
                                        self.dlg.setEnabled(True)
                
                                    where += '('
                                    for index,row in enumerate(rows,start=0):
                                        if index == 0:
                                            if row[0] != 108:
                                                where += '("HABCOMUNA" = ' + str(row[0]) + ' and "HABCOPANA" != 108)'
                                            else:
                                                where += '("HABCOPANA" = 108)'
                                        else:
                                            if row[0] != 108:
                                                where += ' or ("HABCOMUNA" = ' + str(row[0]) + ' and "HABCOPANA" != 108)'
                                            else:
                                                where += ' or ("HABCOPANA" = 108)'
                                    where += ')'
                                else:
                                   QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap zona continental seleccionada.")
                                   self.dlg.GrupPestanyes.setCurrentIndex(3)
                                   self.tornaConnectat()
                                   self.dlg.setEnabled(True)
                                   return
                            elif self.dlg.btoEuropa27.isChecked():
                                SQL_Pro = 'select "CONCODPAI" from "public"."CONTINENTS"  WHERE  "UE27" = 1 ORDER BY 1'
                                try:
                                    cur.execute(SQL_Pro)
                                    rows = cur.fetchall()
                                except Exception as ex:
                                    print("Error SELECT concodpai.")
                                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print (message)
                                    self.tornaConnectat()
                                    QMessageBox.information(None, "Error", "Error SELECT concodpai.")
                                    self.dlg.setEnabled(True)
                                where += '('
                                for index,row in enumerate(rows,start=0):
                                    if index == 0:
                                        if row[0] != 108:
                                            where += '("HABCOMUNA" = ' + str(row[0]) + ' and "HABCOPANA" != 108)'
                                        else:
                                            where += '("HABCOPANA" = 108)'
                                    else:
                                        if row[0] != 108:
                                            where += ' or ("HABCOMUNA" = ' + str(row[0]) + ' and "HABCOPANA" != 108)'
                                        else:
                                            where += ' or ("HABCOPANA" = 108)'
                                where += ')'
                        
                        '''Filtre de nacionalitat'''
                        if self.dlg.btoNACIONALITAT.isChecked():
                            if self.dlg.btoEDAT.isChecked() or self.dlg.btoGENERE.isChecked() or self.dlg.btoESTUDIS.isChecked() or self.dlg.btoORIGEN.isChecked():
                               where += ' AND '
                            if self.dlg.btoPais_3.isChecked():
                                llistaORG = self.dlg.LlistaPais2.selectedItems()
                                if len(llistaORG)>0:
                                    for item in llistaORG:
                                        where += '"HABNACION" = '+ item.toolTip() + ' OR '
                                    where=where[0:len(where)-4]
                                else:
                                   QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap país seleccionat.")
                                   self.dlg.GrupPestanyes.setCurrentIndex(4)
                                   self.tornaConnectat()
                                   self.dlg.setEnabled(True)
                                   return 
                            elif self.dlg.btoZones_3.isChecked():
                                llistaORG = self.dlg.LlistaZonesCont2.selectedItems()
                                if len(llistaORG)>0:                               
                                    zonaCont = 'WHERE '
                                    for item in llistaORG:
                                        zonaCont += '"CONZONCON" = '  + chr(39) + item.toolTip().replace("\'","''")  + chr(39) + ' OR '

                                    zonaCont=zonaCont[0:len(zonaCont)-4]
                                    SQL_Pro = 'SELECT "CONCODPAI" from "public"."CONTINENTS" '  + zonaCont  + ' ORDER BY 1' 
                                    try:
                                        cur.execute(SQL_Pro)
                                        rows = cur.fetchall()
                                    except Exception as ex:
                                        print("Error SELECT concodpai.")
                                        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                        message = template.format(type(ex).__name__, ex.args)
                                        print (message)
                                        self.tornaConnectat()
                                        QMessageBox.information(None, "Error", "Error SELECT concodpai.")
                                        self.dlg.setEnabled(True)
                                    where += '('
                                    for index,row in enumerate(rows,start=0):
                                        if index == 0:
                                            where += '"HABNACION" = ' + str(row[0])
                                        else:
                                            where += ' or "HABNACION" = ' + str(row[0])
                                    where += ')'
                                else:
                                   QMessageBox.information(None, "Error", u"Error:\nNo hi ha cap zona continental seleccionada.")
                                   self.dlg.GrupPestanyes.setCurrentIndex(4)
                                   self.tornaConnectat()
                                   self.dlg.setEnabled(True)
                                   return
                            elif self.dlg.btoEuropa27_3.isChecked():
                                SQL_Pro = 'select "CONCODPAI" from "public"."CONTINENTS"  WHERE  "UE27" = 1 ORDER BY 1'
                                try:
                                    cur.execute(SQL_Pro)
                                    rows = cur.fetchall()
                                except Exception as ex:
                                    print("Error SELECT concodpai.")
                                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print (message)
                                    self.tornaConnectat()
                                    QMessageBox.information(None, "Error", "Error SELECt concodpai.")
                                    self.dlg.setEnabled(True)
                                where += '('
                                for index,row in enumerate(rows,start=0):
                                    if index == 0:
                                        where += '"HABNACION" = ' + str(row[0])
                                    else:
                                        where += ' or "HABNACION" = ' + str(row[0])
                                where += ')'
                        
                        where += "\n"
                        
                        '''Execució de la sentencia SQL'''
                        '''Per ILLES'''
                        if self.dlg.ILLES.isChecked() or self.dlg.TOTS.isChecked():
                            dl = 'delete from "public"."Resum2";'
                            ins = 'insert into  "public"."Resum2"\n'
                            sql = 'select row_number() OVER () AS id, "D_S_I" as ILLES_Codificades, count(*) as Habitants from "public"."Padro"\n'
                            sql_gb = 'group by "D_S_I"\norder by 2'
                            sum = 'select sum("Habitants") from Resum_Tmp;'
                            csv = sql + where + sql_gb
                            try:
                                hab_illes = 0
                                cur.execute(csv)
                                resultat = cur.fetchall()
                                arxiu = open(fileName+ "/tr_illes.csv", 'w')
                                arxiu.write("ILLES_Codificades;Habitants\n")
                                for x in range(0, len(resultat)):
                                    arxiu.write(str(resultat[x][1]) +  ";" + str(resultat[x][2]) + "\n")
                                    hab_illes += resultat[x][2]
                                arxiu.close()
                                if self.dlg.TOTS.isChecked() != True:
                                    QMessageBox.information(None, "Resultat", u"Taula resum creada amb " + str(hab_illes) + ' habitants')
                            except Exception as ex:
                                print("No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                message = template.format(type(ex).__name__, ex.args)
                                print (message)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                QMessageBox.information(None, "Error", u"No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                        '''Per Parcel.les'''
                        if self.dlg.PARCELES.isChecked() or self.dlg.TOTS.isChecked():
                            dl = 'delete from "public"."ResumParcela2"'
                            ins = 'insert into  "public"."ResumParcela2"\n'
                            sql = 'select row_number() OVER () AS id, "REFCAD" as Parcela, count(*) as Habitants from "public"."Padro"\n'
                            sql_gb = 'group by "REFCAD"\norder by 2'
                            sum = 'select sum("Habitants") from "public"."ResumParcela2"'
                            try:
                                hab_parce = 0
                                csv = sql + where + sql_gb
                                cur.execute(csv)
                                resultat = cur.fetchall()
                                arxiu = open(fileName+ "/tr_parceles.csv", 'w')
                                arxiu.write("Parcela;Habitants\n")
                                for x in range(0, len(resultat)):
                                    arxiu.write(str(resultat[x][1]) +  ";" + str(resultat[x][2]) + "\n")
                                    hab_parce += resultat[x][2]
                                arxiu.close()
                                if self.dlg.TOTS.isChecked() != True:
                                    QMessageBox.information(None, "Resultat", u"Taula resum creada amb " + str(hab_parce) + ' habitants')
                            except Exception as ex:
                                print("No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                message = template.format(type(ex).__name__, ex.args)
                                print (message)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                QMessageBox.information(None, "Error", u"No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                        '''Per portals'''
                        if self.dlg.PORTALS.isChecked() or self.dlg.TOTS.isChecked():
                            dl = 'delete from "public"."ResumNPolicia2"'
                            ins = 'insert into  "public"."ResumNPolicia2"\n'
                            sql = 'select row_number() OVER () AS id, "CarrerNumBis" as NPolicia, count(*) as Habitants from "public"."Padro"\n'
                            sql_gb = 'group by "CarrerNumBis"\norder by 2'
                            sum = 'select sum("Habitants") from "public"."ResumNPolicia2"'
                            try:
                                hab_npol = 0
                                csv = sql + where + sql_gb
                                cur.execute(csv)
                                resultat = cur.fetchall()
                                arxiu = open(fileName+ "/tr_npolicia.csv", 'w')
                                arxiu.write("NPolicia;Habitants\n")
                                for x in range(0, len(resultat)):
                                    arxiu.write(str(resultat[x][1]) +  ";" + str(resultat[x][2]) + "\n")
                                    hab_npol += resultat[x][2]
                                arxiu.close()
                                if self.dlg.TOTS.isChecked() != True:
                                    QMessageBox.information(None, "Resultat", u"Taula resum creada amb " + str(hab_npol) + ' habitants')
                                else:
                                    QMessageBox.information(None, "Resultat", u"Taula resum d'illes creada amb " + str(hab_illes) + ' habitants\n'
                                                            + u"Taula resum de parceles creada amb " + str(hab_parce) + ' habitants\n'
                                                            + u"Taula resum de números de policia creada amb " + str(hab_npol) + ' habitants\n')
                            except Exception as ex:
                                print("No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                message = template.format(type(ex).__name__, ex.args)
                                print (message)
                                self.tornaConnectat()
                                self.dlg.setEnabled(True)
                                QMessageBox.information(None, "Error", u"No s'ha pogut modificar la TaulaResum de la base de dades.\nComprova els privilegis que tens.")
                        self.tornaConnectat()
                        self.dlg.setEnabled(True)
                        conn.close()
                        
                    except Exception as ex:
                        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                        message = template.format(type(ex).__name__, ex.args)
                        print (message)
                        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #ff7f7f')
                        self.dlg.lblEstatConn.setText('Error: Hi ha algun camp erroni.')
                        self.dlg.setEnabled(True)
                        #print ("I am unable to connect to the database")
                else:
                    QMessageBox.information(None, "Error", 'No hi ha un destí fitxat pel/s fitxer/s.\nTorneu a crear la taula i doneu un camí vàlid.')
                    self.tornaConnectat()
                    self.dlg.setEnabled(True)
            else:
                QMessageBox.information(None, "Error", 'No hi ha cap connexió seleccionada.\nSeleccioneu una connexió.')
                self.tornaConnectat()
                self.dlg.setEnabled(True)
                #print ("No hi ha cap filtre seleccionat.\nSeleccioneu un filtre.")