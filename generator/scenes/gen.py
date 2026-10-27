import numpy as np, sys, os
from PIL import Image, ImageDraw, ImageFilter
W, H = 5120, 2880
S = 0.25 if '--preview' in sys.argv else 1.0
W, H = int(W*S), int(H*S)
if os.environ.get('PORTRAIT'):
    W, H = int(os.environ.get('PW','1800')), 2400; S = float(os.environ.get('PS','0.85'))
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
Yn, Xn = Y/H, X/W

def hx(c):
    if not isinstance(c,str): return np.asarray(c,np.float32)
    c=c.lstrip('#'); return np.array([int(c[i:i+2],16) for i in (0,2,4)],np.float32)/255
def mix(a,b,t): return a+(b-a)*t
def sm(e0,e1,x): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)

def sky(stops, blobs):
    # stops: list of (pos, color)
    img = np.zeros((H,W,3),np.float32)
    ps=[p for p,_ in stops]; cs=[hx(c) for _,c in stops]
    for i in range(3):
        img[...,i]=np.interp(Yn,ps,[c[i] for c in cs])
    for (cx,cy,rx,ry,col,a) in blobs:
        d=((Xn-cx)/rx)**2+((Yn-cy)/ry)**2
        w=(np.exp(-d)*a)[...,None]
        img=mix(img,hx(col),w)
    return img

def stars(img, alpha, seed, top=0.65):
    if alpha<=0: return img
    r=np.random.default_rng(seed); n=int(1400*S*S*4)
    xs=r.integers(0,W,n); ys=(r.random(n)**1.6*top*H).astype(int)
    b=r.random(n)**3*alpha*(1-ys/(top*H))
    for dx,dy,f in [(0,0,1),(1,0,.5),(0,1,.5),(1,1,.3)]:
        yy=np.clip(ys+dy,0,H-1); xx=np.clip(xs+dx,0,W-1)
        img[yy,xx]=mix(img[yy,xx],np.ones(3),(b*f)[:,None])
    return img

def disc(img,cx,cy,r,col,a=1,glow=0.0,gcol=None):
    d=np.sqrt(((X-cx*W))**2+((Y-cy*H))**2)/(r*W)
    if glow: img=mix(img,hx(col if gcol is None else gcol),(np.exp(-(np.maximum(d-1,0))*3)*glow*(d>1))[...,None])
    m=np.clip((1-d)*r*W,0,1)*a
    # subtle shading
    sh=0.92+0.08*np.clip(((Y-cy*H)/(r*W)),-1,1)*-1
    return mix(img,hx(col)*sh[...,None],m[...,None])

def ring(img,cx,cy,rx,ry,th,col,a,front_only=False,occl=None):
    d=np.sqrt(((X-cx*W)/(rx*W))**2+((Y-cy*H)/(ry*W))**2)
    m=np.clip((th-np.abs(d-1)*rx*W)/1.5,0,1)*a
    if front_only: m=m*(Y>cy*H)
    return mix(img,hx(col),m[...,None])

def noise1d(x,seed,oct=5,base=2.0):
    r=np.random.default_rng(seed); y=np.zeros_like(x)
    amp=1;f=base
    for _ in range(oct):
        y+=amp*np.sin(x*f*2*np.pi+r.random()*6.28)
        y+=amp*0.5*np.sin(x*f*1.37*2*np.pi+r.random()*6.28)
        amp*=0.45; f*=2.1
    return y

def layer(img,ridge,col_top,col_bot,haze_top=None,depth=0.25):
    # ridge: array W of y in px
    m=np.clip(Y-ridge[None,:],0,1)
    t=np.clip((Y-ridge[None,:])/(H*depth),0,1)[...,None]
    c=mix(hx(col_top),hx(col_bot),t)
    return mix(img,c,m[...,None]), m

def ships(img, specs, col='#ffffff', glow=None):
    """specs: (x,y,len,dir,alpha,size) dir: 'up','down','left','right'"""
    ov=Image.new('RGBA',(W*2,H*2),(0,0,0,0)); dr=ImageDraw.Draw(ov)
    c=tuple(int(v*255) for v in hx(col))
    for (x,y,L,d,a,s) in specs:
        x*=W*2;y*=H*2;L*=H*2;s*=S*2*1.0
        vx,vy={'up':(0,-1),'down':(0,1),'left':(-1,0),'right':(1,0)}[d]
        steps=60
        for i in range(steps):
            t0=i/steps;t1=(i+1)/steps
            p0=(x-vx*L*t0,y-vy*L*t0);p1=(x-vx*L*t1,y-vy*L*t1)
            al=int(255*a*(1-t0)**1.6*0.75)
            dr.line([p0,p1],fill=c+(al,),width=max(2,int(s*0.9)))
        # chevron head
        px,py=-vy,vx
        tip=(x+vx*s*7,y+vy*s*7)
        l=(x+px*s*4-vx*s*1,y+py*s*4-vy*s*1); r_=(x-px*s*4-vx*s*1,y-py*s*4-vy*s*1)
        nk=(x+vx*s*1.5,y+vy*s*1.5)
        dr.polygon([tip,l,nk,r_],fill=c+(int(255*a),))
        if glow:
            g=tuple(int(v*255) for v in hx(glow))
            dr.ellipse([x-s*3,y-s*3,x+s*3,y+s*3],fill=g+(int(200*a),))
    ov=ov.resize((W,H),Image.LANCZOS)
    o=np.asarray(ov).astype(np.float32)/255
    return mix(img,o[...,:3],o[...,3:4])

def grain(img,seed=0,amt=0.012):
    r=np.random.default_rng(seed)
    return img+(r.random((H,W,1),dtype=np.float32)-0.5)*amt

def save(img,path):
    img=grain(img)
    Image.fromarray((np.clip(img,0,1)**1*255+0.5).astype(np.uint8)).save(path)
