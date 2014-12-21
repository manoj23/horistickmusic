#!/usr/bin/env python2 -tt
# -*- coding: utf-8 -*-

__copyright__ = "© 2014 Georges Savoundararadj"
__license__   = "MIT"
__version__   = "1.0"

import functools
import logging
import numpy
import os.path
import pygame
import scipy.io.wavfile
import scipy.signal
import sys

freq_sampling = 44100
folder = 'sound/'

class sampleSound(object):
    instances = {}
    def __init__(self, frequency, duration, func):
        if type(self) == sampleSound:
            raise Exception("sampleSound cannot be directly instanciated")
        
        filename = folder + str(self.__class__.__name__) + '_'+ str(frequency) + '_' + str(duration) + '.wav'
        if not os.path.exists(filename):
            t = scipy.linspace(0, duration, freq_sampling * duration)
            sound = map(lambda t: numpy.int16(t * 32767), map(func, t) )
            scipy.io.wavfile.write(filename, freq_sampling, numpy.array(sound))
   
        if not filename in self.instances:
            self.instances[filename] = pygame.mixer.Sound(filename)

        self.sound = self.instances[filename]        
        
class beep(sampleSound):
    def __init__(self, frequency, duration = 0.125):
        func = lambda t: numpy.sin(2 * numpy.pi * t * frequency)   
        super(beep, self).__init__(frequency, duration, func)

class piano(sampleSound):
    def __init__(self, frequency, duration = 1.0, tau = 2.0):
        func = lambda t: numpy.exp(-tau * t) * numpy.sin(2 * numpy.pi * t * frequency) 
        super(piano, self).__init__(frequency, duration, func)

class laser(sampleSound):
    def __init__(self, frequency, duration = 1.0, tau = 2.0):
        func = lambda t: (1-numpy.exp(tau * t)) * numpy.exp(-tau * t) * numpy.sin(2 * numpy.pi * t * frequency) 
        super(laser, self).__init__(frequency, duration, func)

class squar(sampleSound):
    def __init__(self, frequency, duration = 0.25):
        signal = lambda t: numpy.sign(numpy.sin(2 * numpy.pi * t * frequency)) 
        super(squar, self).__init__(frequency, duration, signal)

class squad(sampleSound):
    def __init__(self, frequency, duration = 1.0, tau = 3.0):
        signal = lambda t: numpy.exp(-tau * t) * numpy.sign(numpy.sin(2 * numpy.pi * t * frequency)) 
        super(squad, self).__init__(frequency, duration, signal)
	
class HoriStickSampler(object):
    def __init__(self):
        # Init pygame 
        pygame.display.init()
        pygame.joystick.init()
        pygame.mixer.init(freq_sampling)

        # Init logging facility
        logging.basicConfig()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
       
        # Init joystick 
        if pygame.joystick.get_count() == 0:
            self.logger.critical("Sorry, no Joystick is detected, bye!")
            self.exit()
            
        # Take the first joystick
        self.joystick = pygame.joystick.Joystick(0)   
        self.joystick.init()
        if self.joystick.get_numhats() == 0:
            self.logger.critical("Sorry, your Joystick has no hat, bye!")
        
        self.logger.info("Cool! You can play with your Joystick (only one is selected)!")


        # TODO: get_id, get_name, get_numaxes, get_numballs, get_numbuttons, get_numhat
        self.hatState = (0, 0)

        # Event stuff
        # TODO: set_allowed does not seem to work
        pygame.event.set_allowed([pygame.QUIT, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION])
        
        # Clock stuff
        self.clock = pygame.time.Clock()

        # Make folder 'sound/' 
        if not os.path.exists(folder):
            os.mkdir(folder)

        self.soundMap = {
                     ( -1, -1): { 0: squad(200, 0.5, 4), 1: squad(100, 0.5, 4), 2: squad(300, 0.5, 4), 3: squad(400, 0.5, 4), 
                                  4: squad(800, 0.5, 4), 5: squad(600, 0.5, 4), 6: squad(700, 0.5, 4), 7: squad(500, 0.5, 4)},
                     ( -1,  0): { 0: squad(200), 1: squad(100), 2: squad(300), 3: squad(400), 
                                  4: squad(800), 5: squad(600), 6: squad(700), 7: squad(500)},
                     ( -1,  1): { 0: piano(200, 2), 1: piano(100, 2), 2: piano(300, 2), 3: piano(400, 2), 
                                  4: piano(800, 2), 5: piano(600, 2), 6: piano(700, 2), 7: piano(500, 2)},
                     (  0, -1): { 0: laser(200), 1: laser(100), 2: laser(300), 3: laser(400), 
                                  4: laser(800), 5: laser(600), 6: laser(700), 7: laser(500)},
                     (  0,  0): { 0: piano(200), 1: piano(100), 2: piano(300), 3: piano(400), 
                                  4: piano(800), 5: piano(600), 6: piano(700), 7: piano(500)},
                     (  0,  1): { 0:  beep(200), 1:  beep(100), 2:  beep(300), 3:  beep(400), 
                                  4:  beep(800), 5:  beep(600), 6:  beep(700), 7:  beep(500)},
                     (  1, -1): { 0: squar(200, 0.5), 1: squar(100, 0.5), 2: squar(300, 0.5), 3: squar(400, 0.5), 
                                  4: squar(800, 0.5), 5: squar(600, 0.5), 6: squar(700, 0.5), 7: squar(500, 0.5)},
                     (  1,  0): { 0: squar(200), 1: squar(100), 2: squar(300), 3: squar(400), 
                                  4: squar(800), 5: squar(600), 6: squar(700), 7: squar(500)},
                     (  1,  1): { 0:  beep(200, 2), 1:  beep(100, 2), 2:  beep(300, 2), 3:  beep(400, 2), 
                                  4:  beep(800, 2), 5:  beep(600, 2), 6:  beep(700, 2), 7:  beep(500)} }
        
        self.logger.info("Initialisation OK") 

    def handleButton(self, event):
        button = event.dict['button']
        self.logger.info("button " + str(button) + " pressed")
        if button in range(8):
            self.soundMap[self.hatState][button].sound.play() 
        

    def handleHat(self, event):
        self.hatState = self.joystick.get_hat(0)
        self.logger.info(self.hatState)

    def run(self):
        run = True
  
        while run:
        
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.JOYBUTTONDOWN:
                    self.handleButton(event)
                if event.type == pygame.JOYHATMOTION:
                    self.handleHat(event) 

    def exit(self):
        pygame.quit()
        sys.exit(1)
 

if __name__ == "__main__":
    HoriStickSamplerInstance = HoriStickSampler()
   
    try:
        HoriStickSamplerInstance.run()
    except (KeyboardInterrupt, SystemExit):
        HoriStickSamplerInstance.exit()

    print("Bye, bye!")
