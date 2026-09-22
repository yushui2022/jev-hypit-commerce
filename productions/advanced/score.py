"""Original 132 BPM electronic score. No external music samples are used."""
from pathlib import Path
import wave
import numpy as np
SR=48000;DURATION=42;BPM=132;BEAT=60/BPM
rng=np.random.default_rng(132)
y=np.zeros((SR*DURATION,2),np.float64)

def add(at,sig,volume=1,pan=0):
 start=int(at*SR)
 if start<0:return
 n=min(len(sig),len(y)-start)
 if n<=0:return
 if sig.ndim==1:sig=np.column_stack([sig*np.sqrt((1-pan)/2),sig*np.sqrt((1+pan)/2)])
 y[start:start+n]+=sig[:n]*volume

def tone(freq,duration,decay=3):
 t=np.arange(int(SR*duration))/SR
 return (np.sin(2*np.pi*freq*t)+.18*np.sin(2*np.pi*2*freq*t)+.08*np.sin(2*np.pi*3*freq*t))*np.exp(-t*decay)*np.minimum(t*180,1)

def kick():
 t=np.arange(int(SR*.36))/SR;phase=2*np.pi*(47*t+105*.028*(1-np.exp(-t/.028)))
 return np.sin(phase)*np.exp(-t*13)+rng.standard_normal(len(t))*.12*np.exp(-t*160)

def snare():
 t=np.arange(int(SR*.22))/SR;n=rng.standard_normal(len(t));hp=n-np.convolve(n,np.ones(8)/8,mode='same')
 return hp*np.exp(-t*25)*.35+np.sin(2*np.pi*185*t)*np.exp(-t*35)*.18

def hat(open=False):
 t=np.arange(int(SR*(.18 if open else .07)))/SR;n=rng.standard_normal(len(t));hp=n-np.convolve(n,np.ones(6)/6,mode='same')
 return hp*np.exp(-t*(24 if open else 75))*.12

# Warm minor-nine harmony, swung hats, syncopated bass and short spatial plucks.
chords=[[146.83,174.61,220,261.63,329.63],[174.61,220,261.63,349.23],[130.81,164.81,196,293.66],[146.83,196,246.94,293.66]]
for k in range(int(DURATION/(BEAT*4))+1):
 at=k*BEAT*4;ch=chords[k%4]
 for i,f in enumerate(ch):
  t=np.arange(int(SR*BEAT*4.5))/SR
  sig=(np.sin(2*np.pi*f*t)+.5*np.sin(2*np.pi*(f*1.002)*t))*.07
  env=np.minimum(t/.2,1)*np.minimum((len(t)/SR-t)/.5,1)*np.exp(-t*.5)
  add(at,sig*env,.5 if at<12 else .85,(i-2)*.23)
 for j in range(8):
  a=at+j*BEAT*.5+(0.035 if j%2 else 0);freq=ch[(j+k)%len(ch)]*2
  volume=.09 if a<12 else .14
  if 18<=a<30:volume*=.65
  add(a,tone(freq,1.0,7),volume,(-1 if j%2 else 1)*.5)
  add(a+BEAT*.75,tone(freq,1,8),volume*.23,(-1 if j%2 else 1)*-.7)
for b in range(int(DURATION/BEAT)):
 at=b*BEAT
 if 37.7<at<38.2:continue
 energy=.25 if at<4 else .4 if at<7 else .55 if at<12 else 1
 if 18<=at<30:energy=.48
 if at>=38:energy=.45
 if at>=7:
  if b%4 in [0,2] or (b%8==7 and at>=12):add(at,kick(),.8*energy)
  if b%4 in [1,3]:add(at,snare(),.55*energy)
  for h in range(2 if at<30 else 4):add(at+h*BEAT/(2 if at<30 else 4)+(.023 if h%2 else 0),hat(),energy,(-1 if h%2 else 1)*.35)
  if b%4==3:add(at+BEAT*.65,hat(True),energy*.4,.5)
  ch=chords[(b//4)%4];freq=ch[0]/4
  add(at+(BEAT*.5 if b%4==2 else 0),tone(freq,.4,6),.6*energy)
# Transitions: filtered noise lift into key reveals, with a short impact.
for event in [4,7,12,18,21,24,27,30,32,38]:
 t=np.arange(int(SR*.4))/SR;n=rng.standard_normal(len(t));sig=np.convolve(n,np.ones(20)/20,mode='same')*(t/.4)**2*.28
 add(event-.4,sig,.6,-.3);add(event,tone(65,.6,8),.4)
# Master envelope and gentle saturation.
t=np.arange(len(y))/SR
y*=np.minimum(t/.3,1)[:,None]*np.minimum((DURATION-t)/1.2,1)[:,None]
y=np.tanh(y*1.4);y*=.80/max(np.max(np.abs(y)),1e-9)
out=Path(__file__).resolve().parent/'assets/original-score.wav'
with wave.open(str(out),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes((y*32767).astype('<i2').tobytes())
print('Original score:',out)
