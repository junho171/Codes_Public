#To get whole monitor screen
from PIL import ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab,all_screens = True)
import numpy as np
import pyautogui as pg
import keyboard
import time
import auto_detect

class liner:
    def __init__(self,lu,rb):
        self.nowX,self.nowY = 0,0
        self.endX,self.endY = 0,0
        self.dest_angle = 0
        self.move_angle = 0
        self.map  = None
        self.map_small = None

        self.threshold = 50
        self.stepsize = 14
        self.anglerange = np.pi/4.5
        self.lu = lu
        self.rb = rb
    
    def calc_angle(self,x1,y1,x2,y2):
        try:
            cosV = (x2-x1)/(((x2-x1)**2+(y2-y1)**2)**0.5)
            angle = 2*((y2>=y1)-0.5)*np.arccos(cosV)
        except ZeroDivisionError:
            angle = 0

        return angle
    
    def calc_dest_angle(self):
        return self.calc_angle(self.nowX,self.nowY,self.endX,self.endY)

    def get_map(self):
        ss = pg.screenshot()
        ss = ss.convert('L')
        self.map = np.array(ss)
        self.zip_map = auto_detect.zip_map(ss,self.lu,self.rb,3)
        
        self.map_small = self.zip_map.clean_map()
        print('finished_loading')
        #get_map_image
    
    def get_brightness(self,x,y):
        max_n = 0
        mean_n = 0
        sum_n = 0
        m_j,m_i = 0,0
        
        for i in range(-2,3):
            for j in range(-2,3):
                bt = self.map[y+i][x+j+1920]
                sum_n+=bt
                
                if max_n<bt:
                    max_n = bt
                    if max_n>self.threshold:
                        m_j,m_i = j,i
        mean_n = int(sum_n/25)
                           
        # return max_n,m_j,m_i
        return mean_n,m_j,m_i

    def mouse_click_all(self):
        for y in range(0,len(self.map_small),2):
            for x in range(0,len(self.map_small[0]),2):
                if self.map_small[y][x] == 255:
                    pg.click((self.lu[0]+x,self.lu[1]+y))
                    

class tracker(liner):
    def __init__(self,start,end,map):
        super().__init__()
        self.nowX,self.nowY = start
        self.endX,self.endY = end
        self.map = map
        self.dest_angle = self.calc_angle(self.nowX,self.nowY,self.endX,self.endY)
        self.loclist = []
        
    def check_next(self, angle):
        
        param = 0.4
        nextX = int(self.nowX+param*self.stepsize*np.cos(angle))
        nextY = int(self.nowY+param*self.stepsize*np.sin(angle))
        brightness,add_x,add_y = self.get_brightness(nextX,nextY)
        is_bright = brightness>=self.threshold
        
        
        return nextX,nextY, is_bright, brightness,add_x,add_y
    
    def find_next(self,rng = 50,sign = 1):
        self.dest_angle = self.calc_dest_angle()

        mem_X,mem_Y,mem_bright,mem_is_bright,m_add_x,m_add_y = 0,0,0,False,0,0
        mem_br = False
        
        for i in range(rng):
            angle = self.dest_angle+sign*i*self.anglerange/rng
            nextX, nextY, is_bright, brightness,add_x,add_y = self.check_next(angle)

            if brightness>mem_bright:
                mem_is_bright = is_bright
                mem_bright = brightness
                mem_X,mem_Y = nextX, nextY
                m_add_x,m_add_y = add_x,add_y
                
                if brightness>3*mem_bright:
                    mem_br = True

            angle = self.dest_angle-sign*i*self.anglerange/rng
            nextX, nextY, is_bright, brightness,add_x,add_y = self.check_next(angle)
            
            if brightness>mem_bright:
                mem_is_bright = is_bright
                mem_bright = brightness
                mem_X,mem_Y = nextX, nextY
                m_add_x,m_add_y = add_x,add_y
                
                if brightness>3*mem_bright:
                    mem_br = True
                
            if rng%10 == 9 and mem_br:
                break
            # if is_bright:
            #     self.nowX,self.nowY = nextX,nextY
            #     self.loclist.append((nextX,nextY))
            #     return True
            
        if mem_is_bright:
            self.nowX,self.nowY = mem_X+m_add_x,mem_Y+m_add_y
            self.loclist.append((mem_X+m_add_x,mem_Y+m_add_y))
            # self.nowX,self.nowY = mem_X,mem_Y
            # self.loclist.append((mem_X,mem_Y))
            return True            
    
        return False

    def line_make(self):
        max_cal = int(5*(((self.nowX-self.endX)**2+(self.nowY-self.endY)**2)**0.5)/self.stepsize)+1
        cal = 0
        s = 1
        while ((self.nowX-self.endX)**2+(self.nowY-self.endY)**2)**0.5>self.stepsize*0.5 and cal<max_cal:            
            self.loclist.append((self.nowX,self.nowY))
            f = self.find_next(sign = s)
            if f ==False:
                return self.loclist
            s = -1*s
            cal += 1
            
        if cal<max_cal:
            self.loclist.append((self.endX,self.endY))

        return self.loclist

    def mouse_follow(self):
        self.line_make()
        
        pg.mouseDown(self.loclist[0])
        for n,loc in enumerate(self.loclist[1:-1]):
            if keyboard.is_pressed('e'):
                break
            
            if n%10 ==9:
                pg.moveTo(loc,duration=0.2,_pause=False)
                
        loc = self.loclist[-1]
        pg.moveTo(loc,duration=0.2,_pause=False)
        pg.mouseUp()



    
    # def line_make(self,end):
    #     endX,endY = end
    #     max_cal = int(5*(((self.nowX-endX)**2+(self.nowY-endY)**2)**0.5)/self.stepsize)+1
    #     cal = 0
    #     s = 1
    #     while ((self.nowX-endX)**2+(self.nowY-endY)**2)**0.5>self.stepsize*0.5 and cal<max_cal:            
    #         self.loclist.append((self.nowX,self.nowY))
    #         f = self.find_next(sign = s)
    #         if f ==False:
    #             return self.loclist
    #         s = -1*s
    #         cal += 1
            
    #     if cal<max_cal:
    #         self.loclist.append((endX,endY))

    #     return self.loclist

    # def mouse_follow(self,lst):
    #     for n in range(len(lst)-1):
    #         self.nowX,self.nowY = lst[n]
    #         end = lst[n+1]
    #         self.line_make(end)
        
    #     pg.mouseDown(self.loclist[0])
    #     for n,loc in enumerate(self.loclist[1:-1]):
    #         if keyboard.is_pressed('e'):
    #             break
            
    #         if n%10 ==9:
    #             pg.moveTo(loc,duration=0.2,_pause=False)
                
    #     loc = self.loclist[-1]
    #     pg.moveTo(loc,duration=0.2,_pause=False)
    #     pg.mouseUp()
                