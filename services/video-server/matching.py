import numpy as np

def match(inputs, video):
    sz = len(inputs)
    kernal = np.array([0.5, 0.5, 1, 1, 1, 1, 1, 0.5, 0.5])
    ksz = len(kernal)
    inputsF = []
    videoF = []
    #folding
    for i in range(0,sz):
        tmpI = 0
        tmpV = 0
        for j in range(0,ksz):
            if i+j < sz:
                tmpI += kernal[j] * inputs[i+j]
                tmpV += kernal[j] * video[i+j]
        inputsF.append(tmpI)
        videoF.append(tmpV)
        
    inputsF = np.array(inputsF)
    videoF = np.array(videoF)
    nInputs = inputsF/np.linalg.norm(inputsF)
    nVideo = videoF/np.linalg.norm(videoF)
    corr = np.dot(nInputs, nVideo)
    #print(corr)
    return corr
    
if __name__ == "__main__":
    tInput1 = [0,0,0,1,0,1,0,1,1,1,0,0,0,1,1,1,0,0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    tInput2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
    tInput3 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]


    #match(tInput1,tInput2)
    match(tInput2,tInput3)