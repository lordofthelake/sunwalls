import sys, os, math
from gen import *  # W,H,S,X,Y,Xn,Yn,hx,mix,sm,noise1d,stars?,disc,ring,grain,save
import gen

def col(c): return hx(c) if isinstance(c,str) else np.asarray(c,np.float32)
gen.hx_orig = gen.hx

# ---------- palette interpolation ----------
def lerp(a,b,t):
    if isinstance(a,str) and a.startswith('#'): return col(a)+(col(b)-col(a))*t
    if isinstance(a,np.ndarray): return a+(col(b)-a)*t
    if isinstance(a,(int,float)): return a+(b-a)*t
    if isinstance(a,dict): return {k:lerp(a[k],b[k],t) for k in a}
    if isinstance(a,(list,tuple)):
        a=list(a); b=list(b)
        if len(a)!=len(b) and a and isinstance(a[0],(tuple,list)) and len(a[0])==6:  # blobs: pad with alpha 0
            while len(a)<len(b): a.append(tuple(b[len(a)][:5])+(0,))
            while len(b)<len(a): b.append(tuple(a[len(b)][:5])+(0,))
        return [lerp(x,y,t) for x,y in zip(a,b)]
    return a if t<.5 else b

def palette_at(P,h):
    pre=lerp(P['night'],P['dawn'],.55); morn=lerp(P['dawn'],P['day'],.5); dusk=lerp(P['sunset'],P['night'],.5)
    K=[(0,P['night']),(4.75,P['night']),(5.75,pre),(6.75,P['dawn']),(8.5,morn),(11,P['day']),(15.5,P['day']),
       (17.75,P['sunset']),(19.1,dusk),(20.25,P['night']),(24,P['night'])]
    for (h0,a),(h1,b) in zip(K,K[1:]):
        if h0<=h<=h1: t=(h-h0)/(h1-h0); return lerp(a,b,t*t*(3-2*t))

# ---------- drawing helpers ----------
def C(c): return col(c)
def sky(stops,blobs):
    img=np.zeros((H,W,3),np.float32)
    ps=[p for p,_ in stops]; cs=[C(c) for _,c in stops]
    for i in range(3): img[...,i]=np.interp(Yn,ps,[c[i] for c in cs])
    for (cx,cy,rx,ry,c,a) in blobs:
        if a<=0.003: continue
        d=((Xn-cx)/rx)**2+((Yn-cy)/ry)**2
        img=mix(img,C(c),(np.exp(-d)*a)[...,None])
    return img

def starfield(img,alpha,h,seed,top=.65,pole=(.82,-.15)):
    if alpha<=0.01: return img
    r=np.random.default_rng(seed); n=int(5600*S*S)
    # place stars in polar coords around pole; rotate with hour (15°/h, scaled down for calm)
    rad=np.sqrt(r.random(n))*1.4; th=r.random(n)*2*np.pi + math.radians(h*15*0.35)
    xs=((pole[0]+rad*np.cos(th)*H/W*1.0)*W).astype(int); ys=((pole[1]+rad*np.sin(th))*H).astype(int)
    ok=(xs>=0)&(xs<W-1)&(ys>=0)&(ys<int(top*H)); xs,ys=xs[ok],ys[ok]
    b=r.random(n)[ok]**3*alpha*(1-ys/(top*H))**.8
    for dx,dy,f in [(0,0,1),(1,0,.5),(0,1,.5),(1,1,.3)]:
        img[ys+dy,xs+dx]=mix(img[ys+dy,xs+dx],np.ones(3),(b*f)[:,None])
    return img

def body(img,cx,cy,r,c,a,glow=0,gc=None):
    if a<=0.01: return img
    x0,x1=max(0,int((cx-r*8*H/W)*W)),min(W,int((cx+r*8*H/W)*W)); y0,y1=max(0,int((cy-r*8)*H)),min(H,int((cy+r*8)*H))
    if x0>=x1 or y0>=y1: return img
    sub=img[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
    d=np.sqrt((xx-cx*W)**2+(yy-cy*H)**2)/(r*H)
    if glow: sub=mix(sub,C(gc if gc is not None else c),(np.exp(-np.maximum(d-1,0)*2.2)*glow*a*(d>1))[...,None])
    m=np.clip((1-d)*r*H,0,1)*a
    img[y0:y1,x0:x1]=mix(sub,C(c),m[...,None]); return img

def glows(img,pts):
    """pts: (x,y,radius_px_at_full,color,alpha)"""
    for (x,y,rr,c,a) in pts:
        if a<=0.01: continue
        rr=max(rr*S,0.6); R=int(rr*6)+2; cx,cy=x*W,y*H
        x0,x1=max(0,int(cx-R)),min(W,int(cx+R)); y0,y1=max(0,int(cy-R)),min(H,int(cy+R))
        if x0>=x1 or y0>=y1: continue
        yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32); d2=((xx-cx)**2+(yy-cy)**2)/(rr*rr)
        w=np.clip(np.exp(-d2*1.5)+0.25*np.exp(-d2/9),0,1)*a
        img[y0:y1,x0:x1]=mix(img[y0:y1,x0:x1],C(c),w[...,None])
    return img

def vec(img,fn,y0=0.,y1=1.):
    """Supersampled (2x) vector drawing in a horizontal band. fn(draw, P) with P(x,y)->px coords, k scale."""
    Y0,Y1=int(y0*H),int(y1*H); hh=Y1-Y0
    ov=Image.new('RGBA',(W*2,hh*2),(0,0,0,0)); dr=ImageDraw.Draw(ov)
    P=lambda x,y:(x*W*2,(y*H-Y0)*2)
    fn(dr,P,2*S)
    ov=ov.resize((W,hh),Image.LANCZOS); o=np.asarray(ov).astype(np.float32)/255
    img[Y0:Y1]=mix(img[Y0:Y1],o[...,:3],o[...,3:4]); return img

def rgba(c,a): c=C(c); return tuple(int(max(0,min(1,v))*255) for v in c)+(int(max(0,min(1,a))*255),)

SHIP_SCALE=2.1
SHIP_SCALE=2.1
def craft(dr,P,k,x,y,ang,L,a,c,size=1.0):
    """chevron ship with fading trail. ang in degrees, 0=right, -90=up."""
    vx,vy=math.cos(math.radians(ang)),math.sin(math.radians(ang))
    px,py=P(x,y); Lp=L*H*2; s=size*k*SHIP_SCALE*SHIP_SCALE
    for i in range(50):
        t0,t1=i/50,(i+1)/50
        dr.line([(px-vx*Lp*t0,py-vy*Lp*t0),(px-vx*Lp*t1,py-vy*Lp*t1)],fill=rgba(c,a*(1-t0)**1.6*.6),width=max(2,int(s*1.1*(1-t0*.75))))
    nx,ny=-vy,vx
    dr.polygon([(px+vx*s*7,py+vy*s*7),(px+nx*s*4-vx*s,py+ny*s*4-vy*s),(px+vx*s*1.5,py+vy*s*1.5),(px-nx*s*4-vx*s,py-ny*s*4-vy*s)],fill=rgba(c,a))

def hauler(dr,P,k,x,y,L,c,a):
    """long distant cargo vessel silhouette"""
    px,py=P(x,y); l=L*W*2; h=l*.06
    dr.rounded_rectangle([px-l/2,py-h/2,px+l/2,py+h/2],radius=h/2,fill=rgba(c,a))
    dr.polygon([(px+l/2-h*.2,py-h/2),(px+l/2+h*1.6,py),(px+l/2-h*.2,py+h/2)],fill=rgba(c,a))
    dr.rectangle([px-l*.15,py-h*1.1,px+l*.05,py-h/2],fill=rgba(c,a))
    dr.polygon([(px-l/2,py-h/2),(px-l/2-h*1.2,py-h*1.4),(px-l/2+h*1.5,py-h/2)],fill=rgba(c,a))

def layer(img,ridge,ct,cb,depth=.25):
    m=np.clip(Y-ridge[None,:],0,1); t=np.clip((Y-ridge[None,:])/(H*depth),0,1)[...,None]
    return mix(img,mix(C(ct),C(cb),t),m[...,None])

def sun_pos(h,hz,rise=6.5,sett=18.5,amp=.5,x0=.06,x1=.94):
    u=(h-rise)/(sett-rise); return x0+(x1-x0)*u, hz-amp*math.sin(math.pi*u), (0<u<1)
def moon_pos(h,hz,**kw):
    return sun_pos((h+12)%24,hz,**kw)

xs=np.linspace(0,1,W,dtype=np.float32)
def at(ridge,x): return float(ridge[min(W-1,max(0,int(x*W)))])/H
