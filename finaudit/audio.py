"""Measured PCM waveform descriptors, not psychological deception features.

Uses frame RMS, a declared silence threshold and elementary autocorrelation F0.
This is not Whisper, pYIN, speaker diarization, jitter or shimmer estimation.
"""
from pathlib import Path
import wave
import numpy as np
from .provenance import sha256


def waveform_features(path, frame_ms=40, hop_ms=20, silence_rms=0.01, fmin=60, fmax=400):
    with wave.open(str(path),'rb') as stream:
        sr=stream.getframerate();channels=stream.getnchannels();width=stream.getsampwidth()
        if width!=2 or stream.getcomptype()!='NONE':
            raise ValueError('Provide uncompressed 16-bit PCM WAV; convert external media explicitly')
        raw=stream.readframes(stream.getnframes())
    if not raw: raise ValueError('Empty audio')
    samples=np.frombuffer(raw,dtype='<i2').astype(float).reshape(-1,channels).mean(axis=1)/32768
    n=int(sr*frame_ms/1000);hop=int(sr*hop_ms/1000)
    if n<2 or hop<1 or len(samples)<n or not 0<fmin<fmax<sr/2:
        raise ValueError('Invalid frame/F0 configuration or audio too short')
    rms=[];pitches=[]
    for i in range(0,len(samples)-n+1,hop):
        frame=samples[i:i+n];energy=float(np.sqrt(np.mean(frame**2)));rms.append(energy)
        if energy<silence_rms: continue
        z=(frame-frame.mean())*np.hanning(n)
        corr=np.correlate(z,z,mode='full')[n-1:]
        lo=max(1,int(sr/fmax));hi=min(len(corr)-1,int(sr/fmin))
        if hi<=lo or corr[0]<=0: continue
        lag=lo+int(np.argmax(corr[lo:hi+1]))
        if corr[lag]/corr[0]>=0.6: pitches.append(sr/lag)
    return {'source_sha256':sha256(path),'sample_rate_hz':sr,'channels_downmixed':channels,
            'duration_seconds':len(samples)/sr,'frames':len(rms),'silence_rms_threshold':silence_rms,
            'silence_fraction':float(np.mean(np.asarray(rms)<silence_rms)),
            'rms_mean':float(np.mean(rms)),'rms_std':float(np.std(rms)),
            'voiced_fraction':len(pitches)/len(rms),
            'f0_median_hz':float(np.median(pitches)) if pitches else None,
            'f0_method':'frame autocorrelation; exploratory descriptor, not pYIN',
            'deception_score':None}
