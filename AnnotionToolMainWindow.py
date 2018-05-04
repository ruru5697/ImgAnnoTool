from PyQt5 import QtWidgets,QtCore,QtGui,Qt
from PyQt5.QtWidgets import QMainWindow
import sys
from canvas1 import Canvas
from PyQt5.QtWidgets import QFileDialog
from configure import *

class AnnotionToolMainWindow(QMainWindow):
    def __init__(self,parent=None):
        super(AnnotionToolMainWindow, self).__init__(parent)
        self.setCentralWidget(QtWidgets.QWidget())

        self.predefine_classLabel=QtWidgets.QLabel(self)
        self.predefine_classLabel.setText("predefine class list")
        self.predefine_classListView=QtWidgets.QListView(self)

        self.predefine_keypointLabel=QtWidgets.QLabel(self)
        self.predefine_keypointLabel.setText("prdefine key point")
        self.predefine_keypointListView=QtWidgets.QListView(self)

        self.canvas=Canvas(self)

        self.boundingboxLabel=QtWidgets.QLabel(self)
        self.boundingboxLabel.setText("bounding box list")
        self.boundingboxListView=QtWidgets.QListView(self)
        self.keypointLabel=QtWidgets.QLabel(self)
        self.keypointLabel.setText("key point list")
        self.keypointListView=QtWidgets.QListView(self)

        self.openfileBtn=QtWidgets.QPushButton(self)
        self.openfileBtn.setText("open Image")
        self.selectImagePathBtn=QtWidgets.QPushButton(self)
        self.selectImagePathBtn.setText("open image dir")
        self.selectAnnotionPathBtn=QtWidgets.QPushButton(self)
        self.selectAnnotionPathBtn.setText("open annotion dir")
        self.preImageBtn=QtWidgets.QPushButton(self)
        self.preImageBtn.setText("pre image")
        self.preImageBtn.setShortcut('a')
        self.nextImageBtn=QtWidgets.QPushButton(self)
        self.nextImageBtn.setText("next image")
        self.nextImageBtn.setShortcut('d')

        self.centralLayout=QtWidgets.QVBoxLayout()
        self.toolsLayout=QtWidgets.QHBoxLayout()
        self.buttonsLayout=QtWidgets.QHBoxLayout()
        self.lefttoolsLayout=QtWidgets.QVBoxLayout()
        self.righttoolsLayout=QtWidgets.QVBoxLayout()

        self.centralLayout.addLayout(self.toolsLayout)
        self.centralLayout.addLayout(self.buttonsLayout)

        self.toolsLayout.addLayout(self.lefttoolsLayout,1)
        self.toolsLayout.addWidget(self.canvas,4)
        self.toolsLayout.addLayout(self.righttoolsLayout,1)

        self.lefttoolsLayout.addWidget(self.predefine_classLabel)
        self.lefttoolsLayout.addWidget(self.predefine_classListView)
        self.lefttoolsLayout.addWidget(self.predefine_keypointLabel)
        self.lefttoolsLayout.addWidget(self.predefine_keypointListView)

        self.righttoolsLayout.addWidget(self.boundingboxLabel)
        self.righttoolsLayout.addWidget(self.boundingboxListView)
        self.righttoolsLayout.addWidget(self.keypointLabel)
        self.righttoolsLayout.addWidget(self.keypointListView)

        self.buttonsLayout.addWidget(self.openfileBtn)
        self.buttonsLayout.addWidget(self.selectImagePathBtn)
        self.buttonsLayout.addWidget(self.selectAnnotionPathBtn)
        self.buttonsLayout.addWidget(self.preImageBtn)
        self.buttonsLayout.addWidget(self.nextImageBtn)

        self.centralWidget().setLayout(self.centralLayout)

        self.createMenu()

        self.refreshPredefineClassListView()
        self.connectEvent()


    def createMenu(self):
        self.fileMenu=QtWidgets.QMenu('File')
        self.openFileAction=QtWidgets.QAction('open',self.fileMenu)
        self.selectImagePathAction=QtWidgets.QAction('open dir',self.fileMenu)
        self.selectAnnotionPathAction=QtWidgets.QAction('annotion dir',self.fileMenu)
        self.exitAction=QtWidgets.QAction('exit',self.fileMenu)
        self.fileMenu.addActions([self.openFileAction,self.selectImagePathAction,
                                  self.selectAnnotionPathAction,self.exitAction])
        self.menuBar().addMenu(self.fileMenu)

        self.configMenu=QtWidgets.QMenu('Configure')
        self.configClassAction=QtWidgets.QAction('Class configure',self.configMenu)
        self.configKeypointAction=QtWidgets.QAction('Key point configure',self.configMenu)
        self.importConfigAction=QtWidgets.QAction('Import configure file',self.configMenu)
        self.exportConfigAction=QtWidgets.QAction('Export configure file',self.configMenu)
        self.keypointJointInfoAction=QtWidgets.QAction('Key point joint information',self.configMenu)
        self.configMenu.addActions([self.configClassAction,self.configKeypointAction,
                                    self.importConfigAction,self.exportConfigAction,
                                    self.keypointJointInfoAction])
        self.menuBar().addMenu(self.configMenu)

        self.resetViewListParams()

    def resetViewListParams(self):
        self.bboxListModel=QtCore.QStringListModel()
        self.boundingboxListView.setModel(self.bboxListModel)
        self.kpointLists={}
        self.keypointListModel=QtCore.QStringListModel()
        self.keypointListView.setModel(self.keypointListModel)
        self.bboxList=[]

    def resetViewList(self):
        self.resetViewListParams()
        self.boundingboxListView.setModel(self.bboxListModel)
        self.keypointListView.setModel(self.keypointListModel)

    def connectEvent(self):
        self.openfileBtn.clicked.connect(self.openImage)
        self.predefine_classListView.clicked.connect(self.predefine_classListView_click)
        self.predefine_keypointListView.clicked.connect(self.predefine_keypointListView_click)
        self.boundingboxListView.clicked.connect(self.boundingboxListView_click)
        self.keypointListView.clicked.connect(self.keypointListView_click)
        self.selectImagePathBtn.clicked.connect(self.selectImagePathBtn_click)
        self.selectAnnotionPathBtn.clicked.connect(self.selectAnnotionPathBtn_clicked)
        self.nextImageBtn.clicked.connect(self.nextImageBtn_click)
        self.preImageBtn.clicked.connect(self.preImageBtn_click)

    def selectImagePathBtn_click(self):
        path=QFileDialog.getExistingDirectory(self,'select Image Dir','.')
        if path==None or path=='':
            return
        GeneralConfigure.instance().setImageDir(path)
        image,anno=GeneralConfigure.instance().getNext()
        self.canvas.updateCanvas(image)
        self.predefine_classListView.setFocus()
        self.resetViewList()
        if anno!=None:
            self.canvas.loadAnnotion(anno)

    def selectAnnotionPathBtn_clicked(self):
        path=QFileDialog.getExistingDirectory(self,'select annotion Dir','.')
        if path==None or path=='':
            return
        GeneralConfigure.instance().setAnnotionDir(path)

    def openImage(self):
        file=QFileDialog.getOpenFileName(self,"select a image",".")[0]
        if file==None or file=='':
            return
        GeneralConfigure.instance().setup()
        self.canvas.updateCanvas(file)
        self.predefine_classListView.setFocus()
        self.resetViewList()

    def nextImageBtn_click(self):
        if self.canvas.image==None:
            return
        self.canvas.saveAnnotion()
        image,anno=GeneralConfigure.instance().getNext()
        if image==None:
            return
        self.canvas.updateCanvas(image)
        self.predefine_classListView.setFocus()
        self.resetViewList()
        if anno!=None:
            self.canvas.loadAnnotion(anno)
    def preImageBtn_click(self):
        if self.canvas.image==None:
            return
        self.canvas.saveAnnotion()
        image,anno=GeneralConfigure.instance().getPre()
        if image==None:
            return
        self.canvas.updateCanvas(image)
        self.predefine_classListView.setFocus()
        self.resetViewList()
        if anno!=None:
            self.canvas.loadAnnotion(anno)

    def boundingboxListView_click(self):
        print('bbox')
        index=int(self.boundingboxListView.currentIndex().data().split(':')[1])
        self.keypointListModel.setStringList(self.kpointLists[index])
        self.keypointListView.setModel(self.keypointListModel)
        self.canvas.selectBBox(index)
    def keypointListView_click(self):
        print('kpoint')
        index=int(self.keypointListView.currentIndex().data().split(':')[1])
        self.canvas.selectKpoint(index)

    def predefine_classListView_click(self):
        self.refreshPredefineKeypointListView(
            int(self.predefine_classListView.model().data(self.predefine_classListView.currentIndex(),0).split(':\t')[0])
        )
    def predefine_keypointListView_click(self):
        self.canvas.nextbegin=self.canvas.findNextKeypointIndex(self.predefine_keypointListView.currentIndex().row())
        if self.canvas.nextbegin==None:
            return
        self.predefine_keypointListView.setCurrentIndex(self.predefine_keypointListView.model().createIndex(self.canvas.nextbegin,0))

    def keyReleaseEvent(self, e):
        if e.key()>=QtCore.Qt.Key_0 and e.key()<=QtCore.Qt.Key_9:
            self.refreshPredefineKeypointListView(
                int(self.predefine_classListView.model().data(
                    self.predefine_classListView.model().createIndex(
                        e.key()-QtCore.Qt.Key_0,0
                    ),0).split(':\t')[0])
            )
            print(1)
            self.canvas.create_bbox(e.key()-QtCore.Qt.Key_0,
                                    AnnotionConfigure.instance().getKeypointCntByClassId(e.key()-QtCore.Qt.Key_0))
        elif e.key()==QtCore.Qt.Key_Escape:
            self.canvas.cancel_create_bbox()
        elif e.key()==QtCore.Qt.Key_Delete:
            self.canvas.delete_patch()
        elif e.key()==QtCore.Qt.Key_S:
            if self.predefine_keypointListView.model()==None:
                return
            i=self.canvas.findNextKeypointIndex((self.predefine_keypointListView.currentIndex().row()+1)%self.predefine_keypointListView.model().rowCount())
            if i==None:
                i=0
            self.predefine_keypointListView.setCurrentIndex(self.predefine_keypointListView.model().index(i,0))

    def refreshPredefineClassListView(self):
        classList=AnnotionConfigure.instance().getClassConfig()
        strl=[]
        for i in range(len(classList)):
            strl.append(':\t'.join(classList[i]))
        self.predefine_classListView.setModel(QtCore.QStringListModel(strl))

    def refreshPredefineKeypointListView(self,cid):
        kpointList=AnnotionConfigure.instance().getKeypointConfigByClassId(cid)
        strl=[]
        for i in range(len(kpointList)):
            strl.append(':\t'.join(kpointList[i]))
        self.predefine_keypointListView.setModel(QtCore.QStringListModel(strl))

    def setFocusOnPredefineKeypointListview(self,i=0):
        if i!=None:
            index=self.predefine_keypointListView.model().index(i,0)
            self.predefine_keypointListView.setCurrentIndex(index)
        self.predefine_keypointListView.setFocus()
    def setFocusOnPredefineClassListView(self):
        self.predefine_classListView.setFocus()
    def getPredefineKeypointCurrentItem(self):
        index=self.predefine_keypointListView.currentIndex()
        return index.row()

    def addBBox(self,cid,picker):
        self.bboxList.append('{}:{}'.format(AnnotionConfigure.instance().getClassConfig()[cid][1],picker))
        self.bboxListModel.setStringList(self.bboxList)
        self.boundingboxListView.setModel(self.bboxListModel)
        self.kpointLists[picker]=[]
    def deleteBBox(self,cid,picker):
        self.bboxList.remove('{}:{}'.format(AnnotionConfigure.instance().getClassConfig()[cid][1],picker))
        self.bboxListModel.setStringList(self.bboxList)
        self.boundingboxListView.setModel(self.bboxListModel)
        self.kpointLists.pop(picker)
        self.keypointListModel.setStringList([])
        self.keypointListView.setModel(self.keypointListModel)
    def addKeypoint(self,kid,cls,ppicker,picker):
        self.kpointLists[ppicker].append('{}:{}'.format(AnnotionConfigure.instance().getKeypointConfigByClassId(cls)[kid][1],picker))
        self.keypointListModel.setStringList(self.kpointLists[ppicker])
        self.keypointListView.setModel(self.keypointListModel)
    def deleteKeypoint(self,kid,cls,ppicker,picker):
        self.kpointLists[ppicker].remove('{}:{}'.format(AnnotionConfigure.instance().getKeypointConfigByClassId(cls)[kid][1],picker))
        self.keypointListModel.setStringList(self.kpointLists[ppicker])
        self.keypointListView.setModel(self.keypointListModel)

    def refreshAnnotionViewList(self,bbox,kpoint=None):
        bboxItem='{}:{}'.format(AnnotionConfigure.instance().getClassConfig()[bbox.cls][1],
                                bbox.rect._picker)
        bindex=self.bboxList.index(bboxItem)
        kpindex=None
        if kpoint!=None:
            kpointItem='{}:{}'.format(
                AnnotionConfigure.instance().getKeypointConfigByClassId(bbox.cls)[kpoint.id][1],
                kpoint.rect._picker
            )
            kpindex=self.kpointLists[bbox.rect._picker].index(kpointItem)
        self.boundingboxListView.setCurrentIndex(
            self.boundingboxListView.model().index(bindex,0)
        )
        self.keypointListModel.setStringList(self.kpointLists[bbox.rect._picker])
        self.keypointListView.setModel(self.keypointListModel)
        if kpindex!=None:
            self.keypointListView.setCurrentIndex(
                self.keypointListView.model().index(kpindex,0)
            )

if __name__ == '__main__':
    app=QtWidgets.QApplication(sys.argv)
    main_window=AnnotionToolMainWindow()
    main_window.show()
    sys.exit(app.exec_())
