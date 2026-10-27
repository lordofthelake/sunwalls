"""Refined themes: soft wide marks only, vertical ships, haze/mist depth, occluded detailed structures."""
from dyn import *
from themes2 import RF, TW, MD, CN, HOURS
from scipy.ndimage import map_coordinates, gaussian_filter


PX = lambda v: v*S          # pixel sizes are specified for the 5K canvas
SHIP = float(os.environ.get('SHIP', '1.0'))

# ---------------------------------------------------------------- helpers
def skycol(stops, y):
    ps=[p for p,_ in stops]; cs=[C(c) for _,c in stops]
    return np.array([np.interp(y,ps,[c[i] for c in cs]) for i in range(3)],np.float32)

def hlayer(img, ridge, ct, cb, hazec, haze=0., mist=.25, depth=.25, mistd=.10):
    """Layer fill: vertical gradient, pulled toward the sky's haze colour (more for far layers),
    plus mist rising from the bottom of the layer (Exodus-style atmospheric depth)."""
    d=Y-ridge[None,:]
    m=np.clip(d,0,1)
    t=np.clip(d/(H*depth),0,1)[...,None]
    c=mix(C(ct),C(cb),t)
    c=mix(c,hazec,haze)
    c=mix(c,hazec,(sm(0,H*mistd,d)*mist*.3)[...,None])
    return mix(img,c,m[...,None])

def band(img, dist_px, w_px, col, a):
    """soft wide band: gaussian falloff around a distance field (in px)."""
    m=(1-sm(w_px*.6,w_px,np.abs(dist_px)))*a
    return mix(img,C(col),m[...,None])

def win(cx,cy,rx,ry):
    x0,x1=max(0,int(cx-rx)),min(W,int(cx+rx)); y0,y1=max(0,int(cy-ry)),min(H,int(cy+ry))
    return x0,x1,y0,y1

def trail_up(img, x, y, L, w0, col, a):
    """soft vertical exhaust trail below a rising ship (x,y normalized; L in H units; w0 px)."""
    cx,cy=x*W,y*H; Lp=L*H
    x0,x1,y0,y1=win(cx,cy+Lp/2,w0*4+4,Lp/2+4)
    if x0>=x1 or y0>=y1: return img
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
    t=np.clip((yy-cy)/Lp,0,1)
    m=np.clip(w0/2-np.abs(xx-cx)+.5,0,1)*(1-t)*(yy>=cy)*a
    img[y0:y1,x0:x1]=mix(img[y0:y1,x0:x1],C(col),m[...,None]); return img

def ships_up(img, specs, col, hz=None, hazec=None, glowc=None, glow_a=0., gy=None):
    """specs: (x, y, trail_len, alpha, size). Flat arrow ships pointing straight up with flat trails;
    the closer to the horizon, the more they dissolve into the haze."""
    cols=[]
    for (x,y,L,a,sz) in specs:
        c=C(col)
        if hz is not None: c=mix(c,hazec,float(sm(hz-.42,hz,y))*.3)
        cols.append(c)
    for (x,y,L,a,sz),c in zip(specs,cols):
        if a<=.01: continue
        hl=PX(46)*SHIP
        y0=y+hl*.42/H                                   # clear gap between hull and plume
        floor=(gy if gy is not None else (hz if hz is not None else 1.))-.035
        L=min(L,floor-y0)
        if L>.01: img=trail_up(img,x,y0,L,hl*.2,c,a*.5)
    def draw(dd,Pp,k):
        for (x,y,L,a,sz),c in zip(specs,cols):
            if a<=.01: continue
            hl=PX(46)*SHIP*2; px,py=Pp(x,y)
            dd.polygon([(px,py-hl),(px+hl*.36,py+hl*.12),(px+hl*.1,py+hl*.06),(px-hl*.1,py+hl*.06),(px-hl*.36,py+hl*.12)],fill=rgba(c,a))
    img=vec(img,draw,0,1)
    if glowc is not None and glow_a>0:
        img=glows(img,[(x,y+PX(46)*SHIP*.05/H,3*SHIP,glowc,a*glow_a) for (x,y,L,a,sz) in specs])
    return img

def soft_ring(img, cx, cy, rx, tilt, inner, col, a, part):
    """wide planetary ring as a soft banded annulus. part: 'back' (upper half) or 'front'."""
    X0,Y0=cx*W,cy*H; R=rx*W
    x0,x1,y0,y1=win(X0,Y0,R*1.05,R*tilt*1.1+4)
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
    r=np.sqrt((xx-X0)**2+((yy-Y0)/tilt)**2)/R
    e=PX(16)/R
    b1=sm(inner,inner+e,r)*(1-sm(.78-e,.78,r)); b2=sm(.82,.82+e,r)*(1-sm(1-e,1,r))
    body=1; bands=b1*.8+b2*.55
    f=sm(Y0-6*S,Y0+6*S,yy); side=f if part=='front' else 1-f
    m=body*bands*side*a
    img[y0:y1,x0:x1]=mix(img[y0:y1,x0:x1],C(col),m[...,None]); return img

def vecb(img, fn, y0=0., y1=1., blur=0.):
    """vec() with an optional gaussian blur (px at 5K) for soft shapes."""
    Y0,Y1=int(y0*H),int(y1*H); hh=Y1-Y0
    ov=Image.new('RGBA',(W*2,hh*2),(0,0,0,0)); dr=ImageDraw.Draw(ov)
    P=lambda x,y:(x*W*2,(y*H-Y0)*2)
    fn(dr,P,2*S)
    ov=ov.resize((W,hh),Image.LANCZOS)
    if blur>0: ov=ov.filter(ImageFilter.GaussianBlur(PX(blur)))
    o=np.asarray(ov).astype(np.float32)/255
    img[Y0:Y1]=mix(img[Y0:Y1],o[...,:3],o[...,3:4]); return img

def ground(ridge, x, hw):  # lowest crest point under an element of half-width hw → base fully hidden
    return max(at(ridge,x-hw),at(ridge,x),at(ridge,x+hw))+.012

def scaled(Pp,x0,yb,k):
    return lambda x,y: Pp(x0+(x-x0)*k, yb+(y-yb)*k)

def R(Pp,x0,y0,x1,y1): a=Pp(x0,y0); b=Pp(x1,y1); return [min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]
def U(v): return v*H/W     # convert a vertical-unit size into x units (keeps shapes round)

# ---------------------------------------------------------------- RINGFALL
def ringfall(h):
    from kit import Kit
    P=palette_at(RF,h); p=h/24; hz=.66; hazec=skycol(P['sky'],hz)
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,1,.6)
    sx,sy,up=sun_pos(h,hz+.02,amp=.48)
    img=body(img,sx,sy,.022,P['sun'],1 if up else 0,glow=.5,gc=P['sun'])
    px=.30-.06*math.cos(p*2*math.pi); py=.47+.03*math.sin(p*2*math.pi)
    img=soft_ring(img,px,py,.30,.16,.58,P['rc'],P['pla']*.45,'back')
    img=disc(img,px,py,.13,mix(C(P['pl']),hazec,.15+.85*(1-P['pla'])),1,glow=.08*P['pla'],gcol=P['pl'])
    img=soft_ring(img,px,py,.30,.16,.58,P['rc'],P['pla']*.55,'front')
    bases=[.62,.70,.79,.90]; amps=[.03,.045,.06,.07]; ridges=[]
    for i in range(4):
        n=noise1d(xs,10+i,3,1.2+i*.3); dune=np.abs(np.sin((xs*(1.3+i*.4)+i*.37)*np.pi))**1.5
        ridges.append(((bases[i]-amps[i]*(0.6*dune+0.25*n))*H).astype(np.float32))
    hazes=[.55,.32,.14,0]; mists=[.35,.3,.25,.2]
    L=P['land']; lit=P['lights']
    # ships launching from the settlement, each at its own stage of the climb
    specs=[]
    for j,(x0,off,sz) in enumerate([(.618,0,1),(.672,.37,1),(.645,.7,1),(.70,.18,1)]):
        u=(p*3+off)%1; y=.54-u*.46
        specs.append((x0,y,.07+.10*u,.95*sm(0,.06,u)*sm(1,.8,u),sz))
    img=ships_up(img,specs,P['ship'],hz,hazec,P['warm'],lit*.6)
    for i in range(4):
        if i==1:  # settlement stands on dune 1; drawn first so the dune hides its base
            sc=mix(C(L[1][0]),C(L[2][0]),.45); sc=mix(sc,hazec,.42); sc2=mix(sc,hazec,.035)
            r1=ridges[1]; lights=[]
            wc=mix(mix(sc,hazec,.1),C(P['warm']),.35*min(1,lit*lit))
            def town(d,Pp,k):
                Pp=scaled(Pp,.655,ground(r1,.655,0)+.006,.8)
                K=Kit(d,Pp,sc,sc2,wc,lights,P['warm'],lit); G=lambda x,hw: ground(r1,x,U(hw))
                gl=max(ground(r1,x,0) for x in np.linspace(.552,.76,40))
                d.polygon([Pp(.55,gl+.03)]+[Pp(x,min(ground(r1,x,0),gl)-.006) for x in np.linspace(.55,.762,60)]+[Pp(.762,gl+.03)],fill=rgba(sc,1))
                K.dome(.562,G(.562,.012),.012)
                K.block(.578,G(.578,.009),.016,.022,2,3)
                K.tube(.583,.6,G(.583,0)-.016,G(.6,0)-.02,.006)
                K.dome(.612,G(.612,.026),.026)
                K.tower(.632,G(.632,.008),.092,.0075)
                K.ziggurat(.648,G(.648,.012),.026,3)
                K.tower(.665,G(.665,.006),.06,.006)
                K.dome(.683,G(.683,.02),.02)
                K.block(.7,G(.7,.007),.014,.03,3,2)
                K.dome(.714,G(.714,.011),.011)
                K.block(.737,G(.737,.022),.044,.014,1,5)
                K.half(.737,G(.737,.022)-.014,.012,.012,sc2); K.half(.737,G(.737,.022)-.014,.008,.008)
                K.dish(.754,G(.754,.006),.012,-1)
            img=vecb(img,town,.45,.8,blur=1.4)
            yb=ground(r1,.655,0)+.006
            img=glows(img,[(.655+(x-.655)*.8,yb+(y-yb)*.8,rr*.8,c,a) for x,y,rr,c,a in lights])
        img=hlayer(img,ridges[i],L[i][0],L[i][1],hazec,hazes[i],mists[i])
    return img

# ---------------------------------------------------------------- TIDEWATER
def boat(d,Pp,k,x,y,L,s,c,c2):
    px,py=Pp(x,y); l=L*W*2; h=l*.1
    d.polygon([(px-s*l*.5,py),(px+s*l*.42,py),(px+s*l*.56,py-h*.55),(px-s*l*.3,py-h*.8),(px-s*l*.5,py-h*.55)],fill=rgba(c,1))
    d.polygon([(px-s*l*.24,py-h*.75),(px+s*l*.14,py-h*.75),(px-s*l*.0,py-h*1.75),(px-s*l*.2,py-h*1.75)],fill=rgba(c,1))
    d.polygon([(px-s*l*.17,py-h*1.0),(px+s*l*.06,py-h*1.0),(px-s*l*.03,py-h*1.45),(px-s*l*.15,py-h*1.45)],fill=rgba(c2,1))  # window band
    for q in (-.3,.3):  # foil struts (wide) + foil
        d.polygon([(px+s*l*q-l*.012,py),(px+s*l*q+l*.012,py),(px+s*l*(q-.02)+l*.01,py+h*.8),(px+s*l*(q-.02)-l*.01,py+h*.8)],fill=rgba(c,1))
    d.rounded_rectangle([px-l*.4,py+h*.72,px+l*.4,py+h*.95],radius=h*.1,fill=rgba(c,.95))

def wake(img,x,y,L,s,col,a):
    """soft V wake trailing a boat, rendered as two widening gaussian ridges + a central churn."""
    bx=(x-s*L*.5)*W; by=y*H; Lp=L*W*3.4
    x0,x1=(int(bx-Lp),int(bx)) if s>0 else (int(bx),int(bx+Lp)); x0,x1=max(0,x0),min(W,x1)
    y0,y1=max(0,int(by-L*W*1.0)),min(H,int(by+L*W*1.1))
    if x0>=x1 or y0>=y1: return img
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
    dx=np.clip((bx-xx)*s,0,None); dy=yy-(by+L*W*.09)
    w=PX(4)+dx*.045; fade=np.exp(-dx/(Lp*.3))*sm(0,PX(30),dx)*(1-sm(.7,1,dx/Lp))
    arms=np.exp(-((np.abs(dy)-dx*.16)/w)**2)*np.where(dy>0,.8,.35)
    churn=np.exp(-(dy/(PX(4)+dx*.015))**2)*.6
    m=(arms+churn)*fade*a
    img[y0:y1,x0:x1]=mix(img[y0:y1,x0:x1],C(col),m[...,None]); return img

def sea_field(below, seed=5):
    """perspective-correct soft ripple field in [-1,1]-ish, elongated horizontally, no hard lines."""
    r=np.random.default_rng(seed); G=gaussian_filter(r.standard_normal((700,260)),(1.2,5.0),mode='wrap')
    G/=G.std()
    t=(np.arange(below,dtype=np.float32)+1)/below
    rows=(18/(t+.035))[:,None]*np.ones((1,W),np.float32)
    cols=((np.arange(W,dtype=np.float32)-W/2)/W*260*.55)[None,:]/(t[:,None]+.12)+130
    f=map_coordinates(G,[rows%700,cols%260],order=1,mode='wrap').astype(np.float32)
    return f, t

def tidewater(h):
    from kit import Kit
    P=palette_at(TW,h); p=h/24; hz=.72; hazec=skycol(P['sky'],hz-.01); lit=P['lights']
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,2,.65)
    sx,sy,sup=sun_pos(h,hz+.01,amp=.55); mx,my,mup=moon_pos(h,hz+.01,amp=.45)
    if sup: img=body(img,sx,sy,.03,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.026,P['moon'],.95,glow=.35,gc=P['moon'])
    # craft lifting off from the sea, straight up
    specs=[]
    for j,(x0,off,sz) in enumerate([(.42,0,1.2),(.47,.3,1.0),(.38,.62,.9),(.66,.82,.8)]):
        u=(p*2.5+off)%1; specs.append((x0,hz-.02-u*.5,.05+.09*u,.9*sm(0,.07,u)*sm(1,.8,u),sz))
    img=ships_up(img,specs,P['ship'],hz,hazec,'#9fe0ff',lit*.6)
    isl_r=[]
    hazes=[.5,.25,0]
    for i,c in enumerate(P['isl']):
        n=noise1d(xs,30+i,4,1.5+i)
        hill=np.exp(-((xs-[.15,.82,.05][i])/[.12,.10,.06][i])**2)+0.6*np.exp(-((xs-[.30,.95,.92][i])/[.06,.07,.08][i])**2)
        r=np.where(hill>0.02,(hz-(hill*[.06,.09,.13][i])*(1+.08*n))*H,H+5).astype(np.float32); isl_r.append(r)
        if i==1:  # lighthouse on the far-right island, base hidden by the island itself
            lc=mix(C(c),hazec,hazes[1]*.5); lc2=mix(lc,hazec,.035); x=.845; g=ground(r,x,U(.004))
            wc=mix(mix(lc,hazec,.1),C(P['warm']),.35*min(1,lit*lit)); LL=[]
            def lh(d,Pp,k):
                Pp=scaled(Pp,.87,g+.004,.85)
                K=Kit(d,Pp,lc,lc2,wc,LL,P['warm'],lit); G=lambda x,hw: ground(r,x,U(hw))
                K.lighthouse(x,g,.07,.0055)
                K.cabin(.862,G(.862,.008),.016,.012)
                K.block(.878,G(.878,.008),.016,.016,2,2)
                K.cabin(.893,G(.893,.007),.013,.01)
                K.dish(.906,G(.906,.004),.008,-1)
            img=vecb(img,lh,.5,.8,blur=1.4)
            T_=lambda X_,Y_:(.87+(X_-.87)*.85,g+.004+(Y_-g-.004)*.85)
            img=glows(img,[T_(x,g-.077)+(3.5,'#ffe2b0',lit+.15)]+[T_(a,b_)+(rr,c,al) for a,b_,rr,c,al in LL])
        img=hlayer(img,r,c,c,hazec,hazes[i],.25,mistd=.05)
    img=glows(img,[(.95,hz-.075,3.5,'#ff9a8a',lit*.8)])
    # sea: soft reflection + perspective ripples (no hard streaks)
    hpx=int(hz*H); below=H-hpx
    src=np.flipud(img[max(0,hpx-below):hpx]).copy()
    src=gaussian_filter(src,(PX(3),PX(10),0))
    f,t=sea_field(below); tt=t[:,None,None]
    base=mix(C(P['sea'][0]),C(P['sea'][1]),tt**.8); refl=mix(src,base,.35+.5*tt)
    near=sm(0,.12,t)[:,None]*(0.6+0.6*t[:,None])
    hi=sm(.7,2.0,f)*near; lo=sm(-.7,-2.0,f)*near
    hic=mix(C(P['sea'][0]),C('#ffffff'),.4)
    refl=mix(refl,hic,(hi*.06)[...,None]); refl=mix(refl,C(P['sea'][1]),(lo*.05)[...,None])
    img[hpx:]=refl
    for (bx,up,c) in [(sx,sup,P['sun']),(mx,mup,P['moon'])]:
        if up:
            g=np.exp(-((X[hpx:]-bx*W)/(W*.022*(1+tt[...,0]*3)))**2)*(.55+.25*sm(.3,1.6,f))
            img[hpx:]=mix(img[hpx:],C(c),np.clip(g,0,1)[...,None]*.55)
    return img

# ---------------------------------------------------------------- MERIDIAN
def meridian(h):
    from kit import Kit
    P=palette_at(MD,h); p=h/24; hz=.62; hazec=skycol(P['sky'],hz); lit=P['lights']
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,3,.6)
    sx,sy,sup=sun_pos(h,hz,amp=.5); mx,my,mup=moon_pos(h,hz,amp=.42)
    if sup: img=body(img,sx,sy,.028,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.022,P['moon'],.95,glow=.3,gc=P['moon'])
    # orbital ring: wide soft bands with a brighter core, fading at the ends
    d=np.sqrt(((X-W*.5)/(W*.9))**2+((Y-H*1.25)/(H*1.05))**2); dpx=(d-1)*H*1.05
    ends=sm(0,.25,Xn)*sm(1,.75,Xn)*P['ra']
    img=band(img,dpx,PX(14),P['ring'],.7*ends)
    img=band(img,dpx-PX(40),PX(7),P['ring'],.4*ends)
    def arc_y(x): return 1.25-1.05*math.sqrt(max(0,1-((x-.5)/.9)**2))
    bases=[.66,.74,.83,.93]; amps=[.20,.16,.10,.06]; ridges=[]
    for i in range(4):
        n=noise1d(xs,50+i,6,1.0+i*.5); pk=np.abs(noise1d(xs,60+i,3,.8+i*.4))
        ridges.append(((bases[i]-amps[i]*(.35+.25*n+.35*(1-pk/pk.max())**2))*H).astype(np.float32))
    # one settlement per ridge; farther ridges get smaller settlements (perspective)
    SITES=[(None,.27),((.55,.70),.38),((.12,.30),.53),((.70,.90),.75)]   # (search range, scale) for ridges 0..3
    sites=[]
    for i,(rg,sc_) in enumerate(SITES):
        if rg is None: sites.append((None,sc_)); continue
        m=(xs>rg[0])&(xs<rg[1]); xpi=float(xs[m][np.argmin(ridges[i][m])])
        hw=.034*sc_+.004; lvl=ridges[i][m].min()+.008*H*sc_
        terr=sm(xpi-hw-.018,xpi-hw,xs)*(1-sm(xpi+hw,xpi+hw+.018,xs))
        ridges[i]=(ridges[i]*(1-terr)+lvl*terr).astype(np.float32)
        sites.append((xpi,sc_))
    # tether: soft luminous column from summit to ring, climber pod moving up
    tx=.43; ty=arc_y(tx); gy=at(ridges[0],tx)
    x0,x1,y0,y1=win(tx*W,(ty+gy)/2*H,PX(60),(gy-ty)/2*H)
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32); dxp=xx-tx*W
    col=(1-sm(PX(4),PX(6),np.abs(dxp)))*.6
    img[y0:y1,x0:x1]=mix(img[y0:y1,x0:x1],C(P['ring']),(col*(.5*P['ra']+.3))[...,None])
    cu=(p*4)%1; cy=gy-(gy-ty)*cu
    img=vecb(img,lambda dd,Pp,k:dd.rounded_rectangle(R(Pp,tx-U(.005),cy-.012,tx+U(.005),cy+.012),radius=k*6,fill=rgba(P['ring'],.95)),max(0,cy-.03),min(1,cy+.03))
    img=glows(img,[(tx,cy,5,P['warm'],.3+lit*.7),(tx,ty,7,P['ring'],.3+lit*.5)])
    specs=[]
    for j,(x0_,off,sz) in enumerate([(.30,0,1.3),(.335,.4,1.1),(.27,.7,1.0),(.62,.2,.9),(.74,.55,.8)]):
        u=(p*3+off)%1; specs.append((x0_,.56-u*.45,.06+.1*u,.9*sm(0,.08,u)*sm(1,.8,u),sz))
    img=ships_up(img,specs,P['ship'],hz,hazec,'#bfe0ff',lit*.6)
    hazes=[.45,.28,.12,0]; M=P['mtn']
    for i in range(4):
        rr=ridges[i]; LL=[]; xp,f=sites[i]
        sc=mix(C(M[i][0]),C(M[min(i+1,3)][1]),.4); sc=mix(sc,hazec,hazes[i]*.5); sc2=mix(sc,hazec,.035)
        wc=mix(mix(sc,hazec,.1),C(P['warm']),.35*min(1,lit*lit))
        def build(dd,Pp,k,i=i,rr=rr,xp=xp,f=f):
            K=Kit(dd,Pp,sc,sc2,wc,LL,P['warm'],lit); G=lambda x,hw: ground(rr,x,U(hw))-.012+.0025   # terraces are flat: sit just below the surface
            if i==0:   # tether ground station on the snowy range (farthest, smallest)
                K.block(tx,G(tx,.012*f*2),.05*f,.034*f,2,3); K.ziggurat(tx,G(tx,.012*f*2)-.034*f,.032*f,2,.012*f)
            elif i==1: # observatory + dish + lab
                K.observatory(xp,G(xp,.03*f),.03*f)
                K.block(xp+U(.06*f)*1.0,G(xp+U(.06*f),.012*f),.024*f,.02*f,2,3)
                K.dish(xp-U(.075*f),G(xp-U(.075*f),.008*f),.032*f,1)
            elif i==2: # alpine farming village: greenhouses, cabins, wind turbines
                K.greenhouse(xp-U(.04*f),G(xp-U(.04*f),.02*f),.04*f,.016*f,5)
                K.cabin(xp-U(.008*f),G(xp-U(.008*f),.012*f),.02*f,.016*f)
                K.cabin(xp+U(.014*f),G(xp+U(.014*f),.01*f),.016*f,.012*f)
                K.greenhouse(xp+U(.04*f),G(xp+U(.04*f),.016*f),.03*f,.013*f,4)
                for j,dx in enumerate((-.085,.075,.1)): K.turbine(xp+U(dx*f),G(xp+U(dx*f),.004*f),.05*f,h*.9+j*1.7)
            else:      # front ridge: small spaceport — arched hangar, control tower, fuel tanks
                K.hangar(xp-U(.04*f),G(xp-U(.04*f),.03*f),.06*f,.03*f)
                K.control_tower(xp+U(.012*f),G(xp+U(.012*f),.008*f),.06*f,.008*f)
                K.tanks(xp+U(.05*f),G(xp+U(.05*f),.03*f),.009*f,3)
        img=vecb(img,build,.3,1.0,blur=1.4); img=glows(img,LL)
        img=hlayer(img,ridges[i],M[i][0],M[i][1],hazec,hazes[i],[.4,.35,.3,.2][i],depth=.35,mistd=.12)
    return img

# ---------------------------------------------------------------- CANOPY
def forest_ridge(seed, base, th, per, layer):
    """varied tree line: tiered pines, slim spruces and round broadleaf crowns, irregularly spaced."""
    r=np.random.default_rng(seed); n=int(2.1/per)
    top=np.zeros(W,np.float32)
    for _ in range(n):
        c=r.uniform(-.02,1.02); kind=r.random(); hgt=th*r.uniform(.45,1.1)
        if kind<.62:   # tiered pine
            w=per*r.uniform(.45,.75); v=np.clip(1-np.abs(xs-c)/w,0,1); tiers=r.integers(3,6)
            prof=hgt*np.clip(v-.07*((v*tiers)%1),0,1)*(v>0)
        elif kind<.88: # slim spruce
            hgt*=1.25; w=per*r.uniform(.28,.42); v=np.clip(1-np.abs(xs-c)/w,0,1); prof=hgt*v**1.15
        else:          # round broadleaf crown on a short trunk
            w=per*r.uniform(.5,.8); hgt*=.7; a=np.clip(np.abs(xs-c)/w,0,1)
            prof=hgt*np.clip(1-a**2.2,0,1)**.7*(a<1)
        top=np.maximum(top,prof)
    return ((base-top-th*.16*noise1d(xs,seed+10,3,1.0))*H).astype(np.float32)

def canopy(h):
    from kit import Kit
    P=palette_at(CN,h); p=h/24; hz=.64; hazec=skycol(P['sky'],hz); lit=P['lights']
    img=sky(P['sky'],P['blobs'])
    if P['aur']>.02:
        a=P['aur']; wv=.16+.03*np.sin(Xn*7+h*.6)+.02*np.sin(Xn*17-h)
        band_=np.exp(-((Yn-wv)/.05)**2)*(.75+.25*np.sin(Xn*9+h*.8))*np.exp(-((Xn-.5)/.45)**2)*a*.22
        img=mix(img,C('#5fe0b8'),band_[...,None])
    img=starfield(img,P['st'],h,4,.6)
    sx,sy,sup=sun_pos(h,hz,amp=.5); mx,my,mup=moon_pos(h,hz,amp=.42)
    if sup: img=body(img,sx,sy,.026,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.02,P['moon'],.95,glow=.3,gc=P['moon'])
    specs=[]
    for j,(x0,off,sz) in enumerate([(.69,.1,1.2),(.755,.45,1.0),(.66,.75,.9)]):
        u=(p*2+off)%1; specs.append((x0,.5-u*.4,.06+.1*u,.9*sm(0,.07,u)*sm(1,.8,u),sz))
    img=ships_up(img,specs,P['ship'],hz,hazec,'#ffd9a0',lit*.6)
    for i,c in enumerate(P['hills']):
        img=hlayer(img,(([.62,.67][i]-.05*(.6+.4*noise1d(xs,70+i,3,1.0)))*H).astype(np.float32),c,c,hazec,[.45,.3][i],.3,mistd=.04)
    # spire: tapered shaft with ring platforms and a bulb, hazed into the distance
    spc=mix(C(P['spire']),hazec,.25); spc2=mix(spc,hazec,.25); sx_=.72
    def sp(dd,Pp,k):
        dd.polygon([Pp(sx_-U(.0065),.70),Pp(sx_+U(.0065),.70),Pp(sx_+U(.0022),.31),Pp(sx_-U(.0022),.31)],fill=rgba(spc,1))
        for yv,wv in [(.46,.012),(.55,.016)]:
            dd.ellipse(R(Pp,sx_-U(wv),yv-.004,sx_+U(wv),yv+.004),fill=rgba(spc2,1))
            dd.rectangle(R(Pp,sx_-U(wv*.7),yv,sx_+U(wv*.7),yv+.006),fill=rgba(spc,1))
        dd.ellipse(R(Pp,sx_-U(.0045),.296,sx_+U(.0045),.314),fill=rgba(spc2,1))
    img=vecb(img,sp,.28,.72)
    blink=.6+.4*math.cos(h*2.3)
    img=glows(img,[(sx_,.305,3.5,P['light'],.4+.6*lit*blink),(sx_,.462,2,P['warm'],lit*.7),(sx_,.552,2,P['warm'],lit*.7)])
    hazes=[.35,.15,0]
    for i,(ct,cb) in enumerate(P['trees']):
        base=[.70,.79,.91][i]; th=[.05,.085,.15][i]; per=[.010,.018,.032][i]
        r=forest_ridge(80+i,base,th,per,i)
        if i==0:   # cabins tucked into the far tree line: the trees in front hide their bases
            sc=mix(C(ct),C(P['trees'][1][0]),.5); sc=mix(sc,hazec,.25); sc2=mix(sc,hazec,.035)
            wc=mix(mix(sc,hazec,.1),C(P['warm']),.35*min(1,lit*lit)); LL=[]
            def cab(dd,Pp,k):
                K=Kit(dd,Pp,sc,sc2,wc,LL,P['warm'],lit); Pp0=Pp
                for x_,w_,h_ in [(.18,.016,.013),(.196,.012,.01),(.33,.015,.012),(.47,.018,.014),(.488,.012,.01),(.58,.014,.011),(.86,.016,.013),(.878,.013,.011)]:
                    K.cabin(x_,base-.004,w_*.8,h_*.8)
                K.block(sx_,base+.004,.024,.016,2,4); K.dish(sx_+.024,base+.004,.01,-1)
            img=vecb(img,cab,.55,.8,blur=1.4); img=glows(img,LL)
        img=hlayer(img,r,ct,cb,hazec,hazes[i],[.3,.22,.12][i],depth=.2,mistd=.08)
    lt=[]
    for j in range(9):
        x=(.1+j*.1+.03*math.sin(h*.7+j*2))%1; y=.60+.06*math.sin(h*.5+j*1.3)
        lt.append((x,y,2.6,P['warm'],lit*.9))
    return glows(img,lt)

THEMES={'Ringfall':ringfall,'Tidewater':tidewater,'Meridian':meridian,'Canopy':canopy}

def run(j):
    n,i,hh,OUT=j; save(THEMES[n](hh),f'{OUT}/{n}_{i:02d}.png'); return n,i

if __name__=='__main__':
    from multiprocessing import Pool
    OUT=os.environ.get('OUT') or ('out_port' if os.environ.get('PORTRAIT') else 'out16'); os.makedirs(OUT,exist_ok=True)
    sel=[a for a in sys.argv[1:] if not a.startswith('--')] or list(THEMES)
    jobs=[(n,i,hh,OUT) for n in sel for i,hh in enumerate(HOURS)]
    with Pool(int(os.environ.get('NP','2'))) as pl:
        for r in pl.imap_unordered(run,jobs): print(*r,flush=True)
