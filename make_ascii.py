import sys
from PIL import Image, ImageOps, ImageFilter
import numpy as np
src=sys.argv[1]; cols=int(sys.argv[2]); rows=int(sys.argv[3])
im=Image.open(src).convert('L')
w,h=im.size
# crop: head + shoulders, keep aspect cols:rows*2
im=im.crop((int(w*0.04),int(h*0.04),int(w*0.96),int(h*0.98)))
a=np.asarray(im.resize((cols,rows),Image.LANCZOS)).astype(float)
bg=a>238
fg=a[~bg]
lo,hi=np.percentile(fg,2),np.percentile(fg,98)
n=np.clip((a-lo)/(hi-lo),0,1)
ramp="@%&#Mmw*kjix=+;:,'. "
ramp="@@%#MHkj|i;:,.' "
out=[]
for r in range(rows):
    line=""
    for c in range(cols):
        if bg[r,c]: line+=" "; continue
        v=n[r,c]**0.9
        line+=ramp[min(int(v*(len(ramp)-1)),len(ramp)-2)]
    out.append(line.rstrip())
print("\n".join(out))
