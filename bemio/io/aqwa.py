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

from bemio.data_structures import bem

from math import ceil

class AqwaOutput(object):
    '''
    Class to read and interact with AQWA simulation data
    **Inputs:**

    * out_file: name of the AQWA output file
    
    **Outputs:**
    
    * None
    
    '''
    def __init__(self, hydro_file, list_file):
        self.files = bem.generate_file_names(hydro_file)

        self.data = {}        

        self._read(list_file)

    def _read(self,list_file):
        code = 'AQWA'

        with open(self.files['out'],'r') as fid:
            raw = fid.readlines()

        first_line = 0

        for i, line in enumerate(raw):

            if (first_line == 0) and (line[0] == "*"):
                continue
            else: 
                first_line += 1
            if first_line == 1:
                tmp = np.array(raw[i].split()).astype(np.float)
                num_bodies = int(tmp[0])
                num_wave_directions = int(tmp[1])
                num_frequencies = int(tmp[2])
                num_lines_wave_directions = int(ceil(num_wave_directions/6.))
                num_lines_frequencies = int(ceil(num_frequencies/6.))
                for j in range(num_lines_wave_directions):
                    if j == 0:
                        wave_directions = tmp[3:]
                    else:
                        tmp = np.array(raw[i+j].split()).astype(np.float)
                        np.append(wave_directions,tmp)
                for j in range(num_lines_frequencies):
                    tmp = np.array(raw[i + num_lines_wave_directions + j].split()).astype(np.float)
                    if j == 0:
                        frequencies = tmp
                    else:
                        frequencies = np.append(frequencies,tmp)


            if 'GENERAL' in line:
                tmp = np.array(raw[i+1].split()).astype(np.float)
                water_depth = tmp[0]
                density = tmp[1]
                gravity = tmp[2]
                symmetry = tmp[3]

            if 'DRAFT' in line:
                draft = {}
                for iBod in range(num_bodies):
                    tmp = np.array(raw[i + iBod + 1].split()).astype(np.float)
                    tmp2 = int(tmp[0])
                    draft[tmp2] = tmp[1]

            if 'COG' in line:
                cg = {}
                for iBod in range(num_bodies):
                    tmp = np.array(raw[i + iBod + 1].split()).astype(np.float)
                    tmp2 = int(tmp[0])
                    cg[tmp2] = tmp[1:]

            if line.split()[0] == 'MASS':
                mass_matrix = {}
                for iBod in range(num_bodies):
                    for iRow in range(6):
                        tmp = np.array(raw[i + iBod*6 + iRow + 1].split()).astype(np.float)
                        if iRow == 0:
                            tmp2 = int(tmp[0])
                            mass_matrix[tmp2] = tmp[1:]
                        else:
                            mass_matrix[tmp2] = np.vstack([mass_matrix[tmp2],tmp])

            if 'HYDSTIFFNESS' in line:
                stiffness_matrix = {}
                for iBod in range(num_bodies):
                    for iRow in range(6):
                        tmp = np.array(raw[i + iBod*6 + iRow + 1].split()).astype(np.float)
                        if iRow == 0:
                            tmp2 = int(tmp[0])
                            stiffness_matrix[tmp2] = tmp[1:]
                        else:
                            stiffness_matrix[tmp2] = np.vstack([stiffness_matrix[tmp2],tmp])

            if 'ADDEDMASS' in line:
                added_mass = {}
                for iBod1 in range(num_bodies):
                    for iBod2 in range(num_bodies):
                        for iFreq in range(num_frequencies):
                            for iRow in range(6):
                                tmp = np.array(raw[i + iBod1*(num_bodies*num_frequencies*6) + iBod2*num_frequencies*6 + iFreq*6 + iRow + 1].split()).astype(np.float)
                                if (iBod2==0) and (iFreq==0) and (iRow==0):
                                    tmp2 = tmp[0:3].astype(np.float).astype(np.int)
                                    added_mass[tmp2[0]] = np.zeros([6,6*num_bodies,num_frequencies])
                                    added_mass[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp[3:]
                                elif iRow == 0:
                                    tmp2 = tmp[0:3].astype(np.float).astype(np.int)
                                    added_mass[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp[3:] 
                                else:
                                    added_mass[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp

            if 'DAMPING' in line:
                radiation_damping = {}
                for iBod1 in range(num_bodies):
                    for iBod2 in range(num_bodies):
                        for iFreq in range(num_frequencies):
                            for iRow in range(6):
                                tmp = np.array(raw[i + iBod1*(num_bodies*num_frequencies*6) + iBod2*num_frequencies*6 + iFreq*6 + iRow + 1].split()).astype(np.float)
                                if (iBod2==0) and (iFreq==0) and (iRow==0):
                                    tmp2 = tmp[0:3].astype(np.float).astype(np.int)
                                    radiation_damping[tmp2[0]] = np.zeros([6,6*num_bodies,num_frequencies])
                                    radiation_damping[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp[3:]
                                elif iRow == 0:
                                    tmp2 = tmp[0:3].astype(np.float).astype(np.int)
                                    radiation_damping[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp[3:] 
                                else:
                                    radiation_damping[tmp2[0]][:,iBod2*6+iRow,iFreq] = tmp

            if 'FIDD' in line:
                fidd = {}
                for iBod in range(num_bodies):
                    tmp = np.array(raw[i + iBod + 1].split()).astype(np.float)
                    tmp2 = int(tmp[0])
                    fidd[tmp2] = tmp[1:]

            if 'FORCERAO' in line:
                excitation_magnitude = {}
                excitation_phase = {}
                for iBod in range(num_bodies):
                    for iDir in range(num_wave_directions):
                        for iFreq in range(num_frequencies):
                            tmp1_1 = np.array(raw[i + iBod*(num_wave_directions*num_frequencies*2) + iDir*num_frequencies*2 + iFreq*2 + 1].split()).astype(np.float)
                            tmp1_2 = np.array(raw[i + iBod*(num_wave_directions*num_frequencies*2) + iDir*num_frequencies*2 + iFreq*2 + 2].split()).astype(np.float)
                            tmp2 = tmp1_1[0:3].astype(np.float).astype(np.int)
                            if (iDir==0) and (iFreq==0):
                                excitation_magnitude[tmp2[0]] = np.zeros([num_frequencies,6,num_wave_directions])
                                excitation_phase[tmp2[0]] = np.zeros([num_frequencies,6,num_wave_directions])
                            excitation_magnitude[tmp2[0]][tmp2[2]-1,:,tmp2[1]-1] = tmp1_1[3:]
                            excitation_phase[tmp2[0]][tmp2[2]-1,:,tmp2[1]-1] = tmp1_2


        with open(list_file,'r') as fid:
            raw_list = fid.readlines()
        bod_count = 1
        disp_vol = {}
        for i, line in enumerate(raw_list):
            if 'MESH BASED DISPLACEMENT' in line:
                disp_vol[bod_count] = np.array(line.split())[-1].astype(float)
                bod_count += 1
        

        for i in xrange(num_bodies):
            print 'body' + str(i+1) + ':' 
            self.data[i] = bem.HydrodynamicData() 

            self.data[i].rho = density
            self.data[i].g = gravity
            self.data[i].wave_dir = wave_directions*np.pi/180.
            self.data[i].num_bodies = num_bodies
            
            self.data[i].cg = cg[i+1]
            self.data[i].cb = 'not_defined'
            self.data[i].k = stiffness_matrix[i+1]
            self.data[i].T = 2*np.pi/frequencies
            self.data[i].w = frequencies 
            
            self.data[i].wp_area = 'not_defined' 
            self.data[i].buoy_force = 'not_defined'
            self.data[i].disp_vol = disp_vol[i+1]
            self.data[i].water_depth = water_depth
            self.data[i].body_num = i
            
            self.data[i].name = 'body' + str(i+1)
            self.data[i].bem_code = code
            self.data[i].bem_raw_data = raw

            self.data[i].am.all = added_mass[i+1]
            print '   * Setting added mass at infinite frequency to added mass at omega = ' + str(frequencies[-1])
            self.data[i].am.inf = added_mass[i+1][:,:,-1]
            print '   * Setting added mass at zero frequency to added mass at omega = ' + str(frequencies[0])
            self.data[i].am.zero = added_mass[i+1][:,:,0]
            self.data[i].rd.all = radiation_damping[i+1]
            self.data[i].ex.mag = excitation_magnitude[i+1]
            self.data[i].ex.phase = excitation_phase[i+1]
            print '   * Calculating real and imaginary excitation  components.'
            self.data[i].ex.re = self.data[i].ex.mag * np.cos(self.data[i].ex.phase)
            self.data[i].ex.im = self.data[i].ex.mag * np.sin(self.data[i].ex.phase)

