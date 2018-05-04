import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import sys
from PIL import Image
import matplotlib.patches as patches
from enum import Enum


class CanvasStatus(Enum):
    NONE = 0
    CREATE_BBOX = 1
    CREATE_KPOINT = 2
    MOTIFY_BBOX = 3
    MOTIFY_KPOINT = 4
    SELECT_BBOX = 5
    SELECT_KPOINT = 6


class Canvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = plt.Figure()
        self.subfig = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        self.subfig.figure.canvas.mpl_connect('button_press_event', self.on_button_press_event)
        self.subfig.figure.canvas.mpl_connect("button_release_event", self.on_button_release_event)
        self.subfig.figure.canvas.mpl_connect('motion_notify_event', self.on_motion_notify_event)
        self.subfig.figure.canvas.mpl_connect('pick_event', self.on_pick_event)

        self.status = CanvasStatus.NONE
        self.pickerCnt = 0
        self.bboxs = {}
        self.kpoint = {}
        self.clickpointDist = []
        self.selectPicker = None
        self.noChange = False

    def updateCanvas(self, path):
        self.subfig.cla()
        self.subfig.imshow(Image.open(path))
        self.draw()
        self.status = None
        self.selectPicker = None
        self.clickpointDist = []
        self.pickerCnt = 0
        self.bboxs = {}
        self.kpoint = {}

    def on_button_press_event(self, event):
        if self.status == CanvasStatus.SELECT_BBOX:
            self.bboxs[self.selectPicker].set_alpha(1.)
            self.selectPicker = None
            self.status = CanvasStatus.NONE
        if self.status == CanvasStatus.SELECT_KPOINT:
            self.kpoint[self.selectPicker].set_alpha(1.)
            self.selectPicker = None
            self.status = CanvasStatus.NONE
        if event.button == 1:
            # print('({},{})'.format(event.xdata,event.ydata))
            if self.selectPicker != None:
                # self.subfig.patches.remove(self.bboxs[self.selectPicker])
                pass
            else:
                self.bboxs[self.pickerCnt] = patches.Rectangle([event.xdata, event.ydata], 0., 0., linewidth=5,
                                                               edgecolor='r', facecolor='none', picker=self.pickerCnt)
                self.subfig.add_patch(self.bboxs[self.pickerCnt])
                self.selectPicker = self.pickerCnt
                self.pickerCnt += 1
                self.status = CanvasStatus.CREATE_BBOX
        elif event.button == 3:
            if self.selectPicker != None:
                pass
            else:
                self.kpoint[self.pickerCnt] = patches.Rectangle([event.xdata, event.ydata], 10., 10., linewidth=5,
                                                                edgecolor='b', facecolor='b', picker=self.pickerCnt)
                self.subfig.add_patch(self.kpoint[self.pickerCnt])
                self.pickerCnt += 1

    def on_motion_notify_event(self, event):
        # print('({},{})'.format(event.xdata,event.ydata))
        if self.status == CanvasStatus.CREATE_BBOX:
            self.bboxs[self.selectPicker].set_width(event.xdata - self.bboxs[self.selectPicker].get_x())
            self.bboxs[self.selectPicker].set_height(event.ydata - self.bboxs[self.selectPicker].get_y())
        elif self.status == CanvasStatus.MOTIFY_BBOX:
            self.bboxs[self.selectPicker].set_xy(
                [event.xdata - self.clickpointDist[0], event.ydata - self.clickpointDist[1]])
        elif self.status == CanvasStatus.MOTIFY_KPOINT:
            self.kpoint[self.selectPicker].set_xy([event.xdata, event.ydata])
        self.noChange = False
        self.draw()

    def on_button_release_event(self, event):
        # print('({},{})'.format(event.xdata,event.ydata))
        # print('2')
        if self.noChange == False:
            self.status = CanvasStatus.NONE
            self.selectPicker = None
        else:
            if event.button == 1:
                self.status = CanvasStatus.SELECT_BBOX
                self.bboxs[self.selectPicker].set_alpha(0.5)
            else:
                self.status = CanvasStatus.SELECT_KPOINT
                self.kpoint[self.selectPicker].set_alpha(0.5)

    def on_pick_event(self, event):
        # print(event.artist._picker)
        if event.mouseevent.button == 1:
            if self.status == CanvasStatus.SELECT_BBOX:
                self.bboxs[self.selectPicker].set_alpha(1.)
            self.selectPicker = event.artist._picker
            if self.selectPicker in self.bboxs.keys():
                self.clickpointDist = [event.mouseevent.xdata - self.bboxs[self.selectPicker].get_x(),
                                       event.mouseevent.ydata - self.bboxs[self.selectPicker].get_y()]
                self.status = CanvasStatus.MOTIFY_BBOX
            else:
                self.selectPicker = None
        elif event.mouseevent.button == 3:
            if self.status == CanvasStatus.SELECT_KPOINT:
                self.kpoint[self.selectPicker].set_alpha(1.)
            self.selectPicker = event.artist._picker
            if self.selectPicker in self.kpoint.keys():
                self.status = CanvasStatus.MOTIFY_KPOINT
            else:
                self.selectPicker = None
        else:
            return
        self.noChange = True
