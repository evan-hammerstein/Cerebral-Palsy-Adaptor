import math

# sos = speed of sound
# all distances are in meters
# all times are in seconds


class Transducer():
    '''these three classes represent objects that are placed into the field, each having a position in the x and y frame, as well as a common time array of values at which these objects operate.'''
    def __init__(self, x, y, t_array):
        self.x = x  
        self.y = y  
        self.t_array = t_array
        self.signal = len(self.t_array)*[0] #creates a list of zeroes for each time value to start our signal

class Receiver(Transducer):
    def __init__(self, x, y, t_array):
        super().__init__(x, y, t_array)

class Emitter(Transducer): 
    def __init__(self, x, y, t_array):
        super().__init__(x, y, t_array)

    def generate_signal(self, f_c, n_cycles, amplitude): #calculate the value of the signal at time t based on the equation of a sine wave and how many cycles it goes through based on given info
        final_time = 1 / f_c * n_cycles #calculates the time at which the n_cycles have been completed
        for ti, t in enumerate(self.t_array):
            if t <= final_time:
                self.signal[ti] = amplitude * math.sin(2 * math.pi * f_c * t) 
            else:
                break
        return self.signal

class SoundSimulator():
    def __init__(self, emitters=[], receivers=[], t_array=[], sos = 1500.0): #establishing key values such as positioning and the speed of sound
        self.emitters = emitters
        self.receivers = receivers
        self.t_array = t_array
        self.sos = sos
        
    def run(self): #calculate all of the signals of each emitter in relation to each receiver (including delay) and superimpose them to create one signal sum per receiver
        t_delta = self.t_array[1]-self.t_array[0]
        for r in self.receivers: 
            for e in self.emitters:
                distance = math.sqrt((r.x-e.x)**2 + (r.y - e.y)**2)
                time_delay = math.ceil(distance / self.sos / t_delta)
                signal_temp_one = [1 / distance * value for value in e.signal]
                signal_temp_two = [0.0]*time_delay + signal_temp_one
                r.signal = [x + y for x,y in zip(signal_temp_two,r.signal)] #superimpose them
        return self.receivers
    
class BeamFormer():
    def __init__(self, receivers = [], x_array = [], y_array = [], t_array = [], sos = 1500.0): #initializes the field dimensions based on the range and domain given by the user
        self.receivers = receivers
        self.x_array = x_array
        self.y_array = y_array
        self.t_array = t_array
        self.sos = sos
        self.field = [[[0.0 for _ in self.t_array] for _ in self.x_array] for _ in self.y_array]
    
    def generate_field(self): #generates a field of acoustic source strength values based on position, time, and the receivers in the given space
        c = self.sos
        N = len(self.receivers)
        t_delta = self.t_array[1]-self.t_array[0]
        for yi, y in enumerate(self.y_array):
            for xi, x in enumerate(self.x_array):
                distance_list = [0.0]*len(self.receivers)
                indice_delay_list = [0.0]*len(self.receivers)
                for ri, r in enumerate(self.receivers): #calculate the distance between each receiver and the position given
                    distance = math.sqrt((r.x - x)**2 + (r.y-y)**2)
                    distance_list[ri] = distance
                    indice_delay_list[ri] = distance/c/t_delta
                min_time_delay = min(distance_list)/c/t_delta #find the minimum distance to find the lowest time delay
                for ri, r in enumerate(self.receivers): 
                    p = math.ceil(indice_delay_list[ri]-min_time_delay)
                    distance_final = distance_list[ri]
                    for ti, t in enumerate(self.t_array):
                        if (p+ti) < len(self.t_array):
                            self.field[yi][xi][ti] += distance_final * r.signal[p+ti] / N        #calculates the acoustic source strength for each receiver based on distance, a delayed signal, and the number of receivers            
        return self.field
