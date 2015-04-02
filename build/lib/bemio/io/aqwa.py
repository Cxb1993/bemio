# Copyright 2014 the National Renewable Energy Laboratory

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np

try:

    from astropy.io import ascii

except:

    raise Exception('The astropy module must be installed. Try pip install astropy')

from bemio.data_structures import bem as hd

class AqwaOutput(object):
    '''
    Class to read and interact with AQWA simulation data
    Inputs:
    out_file: name of the AQWA output file
    Outputs:
    None
    '''
    def __init__(self,out_file):
        self.files = hd.generate_file_names(out_file)
        
        self.data = {}        
        
        self.n_bods = 0

        self.code = 'AQWA'
 
        self.readOutFile()
        
        

    def readOutFile(self):
        
        with open(self.files['out'],'r') as fid:
            self.raw = fid.readlines()

        body_num = 0
        body_num2 = 0

        
        for i, line in enumerate(self.raw):
            if 'WATER  DEPTH  . . . . . . . . . . . . . . . . =' in line:
                water_depth = np.array(self.raw[i].split())[-1].astype(float)
                density = np.array(self.raw[i+2].split())[-1].astype(float)
                gravity = np.array(self.raw[i+4].split())[-1].astype(float)
            if '1. STIFFNESS MATRIX AT THE CENTRE OF GRAVITY' in line:
                self.data[self.n_bods] = hd.HydrodynamicData()
                cob = []                
                self.data[self.n_bods].cg = np.array(self.raw[i+2].split())[np.ix_([2,4,6])].astype(float)
                self.data[self.n_bods].disp_vol = np.array(self.raw[i+11].split())[-1].astype(float)
                cob.append(np.array(self.raw[i+14].split())[-1].astype(float))
                cob.append(np.array(self.raw[i+15].split())[-1].astype(float))
                cob.append(np.array(self.raw[i+16].split())[-1].astype(float))
                self.data[self.n_bods].cb = np.array(cob)
                self.data[self.n_bods].wp_area = np.array(self.raw[i+19].split())[-1].astype(float)
                self.data[self.n_bods].water_depth = water_depth
                self.data[self.n_bods].g = gravity 
                self.data[self.n_bods].rho = density
                self.data[self.n_bods].name = 'body' + str(self.n_bods)
                self.data[self.n_bods].bem_code = self.code
                self.data[self.n_bods].bem_raw_data = self.raw
                self.n_bods += 1
            
            if 'AT THE FREE-FLOATING EQUILIBRIUM POSITION' in line:
                runLoop = True
                period = []
                freq = []
                kMatrix = []
                
                ind = 31
                
                self.data[body_num].buoy_force = float(self.raw[i+3].split()[-1])
                
                kMatrix.append(np.array(self.raw[i+16].split()[1:]).astype(float))
                kMatrix.append(np.array(self.raw[i+18].split()[1:]).astype(float))
                kMatrix.append(np.array(self.raw[i+20].split()[1:]).astype(float))
                kMatrix.append(np.array(self.raw[i+22].split()[1:]).astype(float))
                kMatrix.append(np.array(self.raw[i+24].split()[1:]).astype(float))
                kMatrix.append(np.array(self.raw[i+26].split()[1:]).astype(float))
                
                self.data[body_num].k = np.array(kMatrix)                
                count = 0
                
                while runLoop is True:  
                    am = []
                    rd = []
                    if self.raw[i+ind+45].split()[0] != 'WAVE':
                        runLoop = False
                        
                    period.append(self.raw[i+ind].split()[3])
                    freq.append(self.raw[i+ind].split()[-1])
                    
                    am.append(np.array(self.raw[i+ind+10].split()[1:]).astype(float))
                    am.append(np.array(self.raw[i+ind+12].split()[1:]).astype(float))
                    am.append(np.array(self.raw[i+ind+14].split()[1:]).astype(float))
                    am.append(np.array(self.raw[i+ind+16].split()[1:]).astype(float))
                    am.append(np.array(self.raw[i+ind+18].split()[1:]).astype(float))
                    am.append(np.array(self.raw[i+ind+20].split()[1:]).astype(float))
                    am = np.array(am).reshape(6,6,1)
                    
                    rd.append(np.array(self.raw[i+ind+30].split()[1:]).astype(float))
                    rd.append(np.array(self.raw[i+ind+32].split()[1:]).astype(float))
                    rd.append(np.array(self.raw[i+ind+34].split()[1:]).astype(float))
                    rd.append(np.array(self.raw[i+ind+36].split()[1:]).astype(float))
                    rd.append(np.array(self.raw[i+ind+38].split()[1:]).astype(float))
                    rd.append(np.array(self.raw[i+ind+40].split()[1:]).astype(float))
                    rd = np.array(rd).reshape(6,6,1)

                    if count is 0:
                        amAll = am
                        rdAll = rd
                    else:
                        amAll = np.append(amAll,am,axis=2)
                        rdAll = np.append(rdAll,rd,axis=2)
                    
                    ind += 45
                    count += 1
                    
                self.data[body_num].T = np.array(period).astype(float)
                self.data[body_num].w = np.array(freq).astype(float)
                self.data[body_num].am.all = amAll
                self.data[body_num].rd.all = rdAll
                self.data[body_num].am.infFreq = self.data[body_num].am.all[:,:,-1]
                self.data[body_num].am.zeroFreq = self.data[body_num].am.all[:,:,0]

                self.data[body_num].nW = np.size(self.data[body_num].w)
                self.data[body_num].body_num = body_num

                body_num += 1

            if '* * * * H Y D R O D Y N A M I C   P A R A M E T E R S   F O R   S T R U C T U R E'  in line:
                if 'FROUDE KRYLOV + DIFFRACTION FORCES-VARIATION WITH WAVE PERIOD/FREQUENCY' in self.raw[i+4]:
                    temp3 = ascii.read(self.raw[i+12:i+11+np.size(self.data[0].w)]) # Change this index from 0 to the correct index
                    temp = self.raw[i+11].split()
                    temp2 = float(temp.pop(2))
                    exMag = []
                    exPhase = []
                    exAll = {}
                    if temp2 == 180:
                        exAll[body_num2] = temp3
                        exAll[body_num2].add_row(temp)
                        temp = exAll[body_num2].copy()
                        exAll[body_num2][0] = temp[-1]
                        for k,line in enumerate(exAll[body_num2]):
                            if k > 0:
                                exAll[body_num2][k] = temp[k-1]  
                        for m,freq in enumerate(exAll[body_num2].field(1)):
                            exMag.append(np.array([exAll[body_num2].field(2)[m],
                                                       exAll[body_num2].field(4)[m],
                                                       exAll[body_num2].field(6)[m],
                                                       exAll[body_num2].field(8)[m],
                                                       exAll[body_num2].field(10)[m],
                                                       exAll[body_num2].field(12)[m]]))
                            exPhase.append(np.array([exAll[body_num2].field(3)[m],
                                                       exAll[body_num2].field(5)[m],
                                                       exAll[body_num2].field(7)[m],
                                                       exAll[body_num2].field(9)[m],
                                                       exAll[body_num2].field(11)[m],
                                                       exAll[body_num2].field(13)[m]]))

                        self.data[body_num2].waveDir = np.deg2rad(temp2)
                        self.data[body_num2].ex.mag = np.array(exMag)
                        self.data[body_num2].ex.phase = np.array(exPhase)
                        self.data[body_num2].ex.re = self.data[body_num2].ex.mag*np.cos(np.deg2rad(self.data[body_num2].ex.phase))
                        self.data[body_num2].ex.im  = self.data[body_num2].ex.mag*np.sin(np.deg2rad(self.data[body_num2].ex.phase))
                        body_num2 += 1
        
    
    def writeWecSimHydroData(self):
        hd.writeWecSimHydroData(self.data,self.files['wecSim'])     
        
    def writeHdf5(self):
        hd.writeHdf5(self.data,self.files['hdf5'])
