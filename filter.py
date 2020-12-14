# csv-datei encoding: iso-8859-1
# mit charset-detector bestimmt 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import math

from pandas import Series, DataFrame 
from scipy.signal import medfilt2d, wiener, hilbert2
from matplotlib.pyplot import figure
from matplotlib.colors import ListedColormap

import sys
import codecs
import time
import csv

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from tkinter.filedialog import askopenfilename

from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
from datetime import datetime

import zipfile

a='test'
x=[None] * 3
saveP=0
saveD=0
r=0
c=0
dname=''
pixlsize=''
unit=''
j=0
terminalLogs = list()
asdf=''

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("guiOptimized.ui", self)
        self.setFixedSize(810, 628) #460
        self.setWindowIcon(QIcon('tu-kaiserslautern-squarelogo.png'))        
        self.TUlogo.setIcon(QIcon('tu_logo.png')) 
        
        #self.terminalOut.setStyleSheet("color: green;")

        self.file_path = None

        self.log("Programmstart")
        self.log("Bitte Messwerte einlesen")

        self.main()
        
        #self.browse.clicked.connect(self.browsefiles)
        #print(self.file_path)

        #if(self.filter2.isChecked()):
            #print("AHSDHLASKD")        
            #filterFunction=self.filter(path, rows, columns)

        #self.browse.clicked.connect(lambda: filterFunction)
    
    def log(self, text):
        global terminalLogs; global j 

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        logText = '['+current_time+'] ' + text

        terminalLogs.append(logText)
        self.terminalOut.append(str(logText))
        j += 1

    #def throwErr(self, err):

    def entzip(self):
        with zipfile.ZipFile('zipfile.zip','r') as zfile:
            zfile.extractall('path')

    def plotSave(self):
        global saveP
        if (self.savePlot.isChecked()):
            saveP=1
            self.log("Plott wird exportiert")
        else:
            self.log("Plott wird NICHT exportiert")
    
    def dataSave(self):
        global saveD
        if (self.saveData.isChecked()):
            saveD=1
            self.log("Daten werden exportiert")
        else:
            self.log("Daten werden NICHT exportiert")

    def rauheit(self):
        global r; global c
        global asdf

        if not (asdf == ''):
            self.log("Rauheit wird berechnet")
            messdaten_raw=np.loadtxt(open(asdf, "rb"), delimiter=",", skiprows=2, encoding='utf-8')

            M=int(r)
            N=int(c)
            z=0.0
            betrag=0.0
            betrag2=0.0

            for m in range(1,M):
                for n in range(1,N):
                    z += float(messdaten_raw[m,n])
        
            mittelwert_z = ( 1 / (M*N) ) * z

            for m in range(1,M):
                for n in range(1,N):
                    betrag += abs(float(messdaten_raw[m,n]) - mittelwert_z)

            mittenrauheit_ra = (1/(M*N)) * betrag

            for m in range(1,M):
                for n in range(1,N):
                    betrag2 += (float(messdaten_raw[m,n]) - mittelwert_z) ** 2

            quadratrauheit_rq = math.sqrt((1/(M*N)) * betrag2)

            self.mittenrauwert_ra.setText("Ra = " + str(mittenrauheit_ra))
            self.quadratrauwert_rq.setText("Rq = " + str(quadratrauheit_rq))
            # gemittelte Rautiefe Rz ist mittlerweile als ISO-Kennwert gelöscht
        else:
            self.log("Bitte Datei einlesen!")

    #def checkFilter(self):
    #    global x; global saveP; global saveD; global asdf
    #    if (self.radiomedfilt.toggled):
    #        #self.log("Datenfilter [Medfilt] ausgewaehlt")
    #        print("HLLO")
    #        #print(asdf, x[1], x[2], saveP, saveD)
    #        #self.filter(asdf, x[1], x[2], saveP, saveD)
    #    else:
    #        print("nope")

    def main(self):
        global x; global saveP; global saveD; global asdf

        self.browse.clicked.connect(self.browsefiles)

        self.savePlot.clicked.connect(self.plotSave)
        self.saveData.clicked.connect(self.dataSave)

        self.ra.clicked.connect(self.rauheit)

        #self.radiomedfilt.clicked.connect(self.log("Datenfilter Medfilt ausgewaehlt"))

        #Lambda functions are used when you need a function for a short period of time.
        self.dataFilter.clicked.connect(lambda: self.filter(asdf, x[1], x[2], saveP, saveD))

        #self.dataFilter.clicked.connect(self.checkFilter)

    def filter(self, file, row, column, save1, save2):
        if not (file == None):
            # Matrix aus messdaten.csv erstellen
            datei=file
            dateiname=(datei.split("/")[-1]).split(".csv")[0]

            messdaten_raw=np.loadtxt(open(datei, "rb"), delimiter=",", skiprows=2, encoding='utf-8')

            # Matrix Größe ermitteln

            rows=int(row)
            columns=int(column)

            #datenTitel=datei
            datenTitel=dateiname
            datenTitel_medfilt='Filter: Medfilt'
            datenTitel_arrayDiff='Messwerte mit grosser Abweichung'

            # Matrix / Messdaten plotten

            # "Figure" erzeugen, 2x2 Grid
            f, axs = plt.subplots(2, 2, figsize=(15,15), sharey=True)

            ax1=axs[0, 0]; ax2=axs[0, 1]
            ax3=axs[1, 0]; ax4=axs[1, 1]

            # Hauptueberschrift
            f.suptitle(datenTitel, fontsize=50)

            # Rohdaten
            axs[0, 0].matshow(messdaten_raw)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax1.set_title("Rohe Messdaten", fontsize=24)
            ax1.set_xlabel('x / µm')
            ax1.set_ylabel('y / µm')

            #axs[0, 0].set_title("Rohe Messdaten", fontsize=24)
            #axs[0, 0].set_xlabel('x / µm')
            #axs[0, 0].set_ylabel('y / µm')

            # Abweichungen Filtern / Korrigieren

            # Filter: Medfilt 
            messdaten_medfilt=medfilt2d(messdaten_raw, kernel_size=3)

            # erste und letzte Einträge korrigieren
            data00=messdaten_raw[0][0]; data01=messdaten_raw[0][-1]
            data10=messdaten_raw[-1][0]; data11=messdaten_raw[-1][-1]

            messdaten_medfilt[0][0]=data00; messdaten_medfilt[0][-1]=data01
            messdaten_medfilt[-1][0]=data10; messdaten_medfilt[-1][-1]=data11

            ax2.matshow(messdaten_medfilt)
            ax2.set_title(datenTitel_medfilt, fontsize=24)
            ax2.set_xlabel('x / µm')
            ax2.set_ylabel('y / µm') 

            # Werte in der Matrix, die sich unterscheiden
            messdaten_diff=np.equal(messdaten_raw, messdaten_medfilt)

            #colormap = colors.ListedColormap(["red","green"])
            #cmap = ListedColormap(['white', 'black'])

            ax3.matshow(messdaten_diff)#, cmap=cmap)
            ax3.set_title('Geaenderte Messwerte', fontsize=24)
            ax3.set_xlabel('x')
            ax3.set_ylabel('y')

            # "Staerke" der Abweichung
            array_difference = messdaten_raw - messdaten_medfilt 

            ax4.matshow(array_difference)
            ax4.set_title(datenTitel_arrayDiff, fontsize=24)
            ax4.set_xlabel('x / µm')
            ax4.set_ylabel('y / µm')

            #messdaten_raw

            # 2x2 Matrix in 1D umwandeln 
            array_flat = array_difference.flatten() 

            # sorted array 
            sorted_index_array = np.argsort(array_flat) 
            
            # sorted array 
            sorted_array = array_flat[sorted_index_array] 

            n = 10

            # find n largest value 
            rslt = sorted_array[-n : ] 
            rslt_min = sorted_array[ : -n] 
            
            # show the output 
            #print(n, "groessten Werte:", rslt)
            #print(n, "kleinste Werte:", rslt_min)

            num=[None] * n

            posx=[None] * n
            posy=[None] * n

            diff_stringList = np.round(array_difference, 3)

            def getPos(z, value, list):
                for i in range(0, rows):
                    for j in range(0, columns):
                        if not (list[i][j] == 0.0):
                            posx[z] = j
                            posy[z] = i
                            
            for i in range(0,n):
                num[i]='%.3f'%rslt[i]

                equal = diff_stringList == float(num[i])
                drop = np.where(diff_stringList == float(num[i]), diff_stringList, 0)

                getPos(i, num[i], drop)

            for i in range(0,n):
                ax4.scatter(posx[i], posy[i] , s=400, facecolor='none', edgecolors='white')

            # große Abweichungen anzeigen
            for i in range(0,n):
                label = f"({num[i]})"
                plt.annotate(label, # this is the text
                            (posx[i], posy[i]),
                            textcoords="offset points", # how to position the text
                            color='white',
                            xytext=(0,15), # distance from text to points (x,y)
                            ha='center') # horizontal alignment can be left, right or center

            global pixlsize; global unit

            if(save1):
                print("datei wird gerade gespeichert")
                plt.savefig(dateiname+"_medfilt.png")
            if(save2):
                print("datei wird gerade gespeichert")
                matrixInfo='Matrixgröße: ' + str(rows)+'x'+str(columns)
                pixelInfo='Pixelgröße: ' + str(pixlsize) #+ ' ' + str(unit)
                
                #csvData = matrixInfo + '\n' + pixelInfo

                with open(dateiname+'_medfilt.csv', 'w', newline='', encoding='iso-8859-1') as file:
                    writer = csv.writer(file, delimiter=',')#, quoting=csv.QUOTE_NONE)

                    writer.writerow([matrixInfo])
                    writer.writerow([pixelInfo])

                    writer.writerows(messdaten_medfilt)

                    #for row in messdaten_medfilt:
                    #    print(" ".join(map(str, row)))

                    #print(str)
                    #writer.writerow(str)

            # import re

                #fin = open(dateiname+'_medfilt.csv', "rt", encoding='iso-8859-1')
                #noApo = re.sub('"', '', fin.read())
                #fin.close()

                #fin = open(dateiname+'_medfilt.csv', "wt", encoding='iso-8859-1')
                #fin.write(noApo)
                #fin.close()

                #with open(dateiname+'_medfilt.csv', "r", encoding='iso-8859-1') as f:
                #    lines = f.readlines()
                #del lines[2]
                #with open(dateiname+'_medfilt.csv', "w", encoding='iso-8859-1') as f:
                #    for line in lines:
                #       f.write(line)

                #data = data.replace('"', '')
                #fin.close()
                #fin = open(dateiname+'_medfilt.csv', "wt", encoding='iso-8859-1')
                #fin.write(data)

                    #fieldnames = ['matrixsize', 'pixelsize', 'filterData']
                    #writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\n')
                    #writer.writerow({'matrixsize' : 'Matrixgroesse: 5x2'})
                    #writer.writerow({'pixelsize' : 'Pixelgroesse: 9a'})
                    #writer.writerow({'filterData' : 'Pixelgroesse: 9a'})
                    #writer.writerow({first_name})

                    #writer.writerow(csvData) # s macht den unterschied
                    #writer.writerows(messdaten_medfilt)

            plt.show()

        else:
            self.log("Bitte Datei einlesen!")

    def showfileInfo(self, path):
        with codecs.open(path, mode='r', encoding='iso-8859-1') as f:
            head = [next(f) for x in range(2)]

        dateiname=path.split('/')[-1]
        
        global x
        global terminalLogs; global j

        matrixsize=head[0]
        rows=(matrixsize.split(' ')[1]).split('x')[0]
        columns=(matrixsize.split(' ')[1]).split('x')[1]

        x[0]=dateiname

        x[1]=rows
        x[2]=columns

        global r; global c
        c=columns
        r=rows

        pixlsize=head[1].split(' ')[1]
        unit=head[1].split(' ')[2]

        self.log("Datei erfolgreich eingelesen")
        self.log("Bitte Filter und Export-Optionen waehlen")

        #global pixlsize; global unit
        #terminalLogs.append("Messwertinfos auslesen")
        #self.terminalOut.append(str(terminalLogs[j]))
        #j+=1

        self.fileInfo.setText("Dateiname: "+dateiname+"\n"+matrixsize+head[1])
        
        #self.file_path = path
        #data=path+';'+rows+';'+columns
        #return data
#        if(self.radiomedfilt.isChecked()):
        #if(self.filter2.isChecked()):
        #    print("AHSDHLASKD")        
       
        #save=0
        #if(self.savePlot.isChecked()):
        #    print("Plot wird gespeichert")
        #    save=1

        #filterFunction=(path, rows, columns)
        #return filterFunction
        #else:
        #    print("NOPE")

        #self.dataFilter.clicked.connect(lambda: filterFunction)

    def browsefiles(self):
        # s for several FileNames
        global asdf

        fname = QFileDialog.getOpenFileName(self, 'Messwerte einlesen', '/home/ian/Dokumente/Semester_7/Seminar 2.2/python/', "CSV-Dateien (*.csv)")
        self.filename.setText(fname[0]) 
        
        asdf=fname[0]
        
        print("TETETE" + asdf)
        #terminalLogs += "\n[CSV-Datei ausgewählt]"+fname[0]
        #self.terminalOut.setText(terminalLogs)

        MainWindow.showfileInfo(self, fname[0])
        #x = MainWindow.showfileInfo(self, fname[0])
        #print(x)

        #if(self.dataFilter.clicked.connect(lambda: self.filter(x[0], x[1], x[2], x[3]))):
        #    print("ES GEHT LOOOS")

        #save=0
        #if(self.savePlot.isChecked()):
        #    print("Plot wird gespeichert")
        #    save=1

        #self.dataFilter.clicked.connect(lambda: self.filter(x[0], x[1], x[2], save))

        #return x

currentFile=''
app = QtWidgets.QApplication(sys.argv)

w = MainWindow()
w.show()

sys.exit(app.exec_())