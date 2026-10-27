from dyn import *

# =============== RINGFALL — desert, ringed giant, a domed settlement, ships landing
RF={
 'dawn':dict(sky=[(0,'#5d4e7a'),(.35,'#c98a8f'),(.62,'#f2c6a0'),(1,'#f6dcc0')],blobs=[(.2,.6,.5,.25,'#ffd9a8',.6),(.8,.1,.4,.3,'#7d5a8f',.4)],
   pl='#e9c7c0',pla=.5,rc='#b9a3b8',sun='#fff1dc',st=.15,land=[('#e7c3b0','#d9ae9e'),('#cf9f93','#b78682'),('#a9737a','#8a5c69'),('#6f4a5e','#4b3448')],ship='#fff4ea',lights=.35,warm='#ffd9a0'),
 'day':dict(sky=[(0,'#4f86b8'),(.4,'#8dbcd6'),(.7,'#d9e3df'),(1,'#efe4d2')],blobs=[(.5,.15,.5,.3,'#a6d0e4',.4),(.5,.6,.3,.2,'#ffffff',0)],
   pl='#f1e8e2',pla=.3,rc='#ffffff',sun='#fffdf5',st=0,land=[('#ead6c0','#e0c5aa'),('#dbb895','#c99f7c'),('#c08a66','#a8714f'),('#8a5a43','#6b4333')],ship='#ffffff',lights=0,warm='#ffffff'),
 'sunset':dict(sky=[(0,'#2f3466'),(.3,'#8a4f7d'),(.55,'#e2816a'),(.72,'#f5b77a'),(1,'#f8d39a')],blobs=[(.82,.62,.5,.2,'#ffcf85',.7)],
   pl='#f4b9a0',pla=.7,rc='#d18aa0',sun='#ffe6b8',st=.2,land=[('#d9927a','#c47a6c'),('#a9616a','#8d4d5e'),('#6e3e57','#55304a'),('#38243f','#251a30')],ship='#fff0dd',lights=.55,warm='#ffcf8a'),
 'night':dict(sky=[(0,'#0b1028'),(.45,'#1b2450'),(.75,'#3b3f6e'),(1,'#5a5480')],blobs=[(.3,.5,.4,.25,'#4a5a9a',.4)],
   pl='#a7b0d6',pla=.9,rc='#8a95c8',sun='#ffffff',st=.95,land=[('#4a4672','#3e3a63'),('#363357','#2c2a4a'),('#25233f','#1c1b33'),('#141327','#0d0c1c')],ship='#cfe0ff',lights=1,warm='#ffc878'),
}
def ringfall(h):
    P=palette_at(RF,h); p=h/24; hz=.66
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,1,.6)
    # moving sun (small, distant star) / moon not needed: giant planet is the night light
    sx,sy,up=sun_pos(h,hz+.02,amp=.48)
    img=body(img,sx,sy,.022,P['sun'],1 if up else 0,glow=.5,gc=P['sun'])
    px=.30-.06*math.cos(p*2*math.pi); py=.47+.03*math.sin(p*2*math.pi)
    img=ring(img,px,py,.30,.045,3*S,P['rc'],P['pla']*.7)
    img=disc(img,px,py,.13,P['pl'],P['pla'],glow=.15,gcol=P['pl'])
    img=ring(img,px,py,.30,.045,3*S,P['rc'],P['pla']*.9,front_only=True)
    # distant hauler crossing high
    hx_=(p*1.6+.15)%1.4-.2
    img=vec(img,lambda d,Pp,k:hauler(d,Pp,k,hx_,.18,.07,P['ship'],.4),.1,.26)
    img=glows(img,[(hx_-.02,.18,3,P['warm'],P['lights']*.6),(hx_+.02,.18,3,P['warm'],P['lights']*.6)])
    bases=[.62,.70,.79,.90]; amps=[.03,.045,.06,.07]; ridges=[]
    for i,(ct,cb) in enumerate(P['land']):
        n=noise1d(xs,10+i,3,1.2+i*.3); dune=np.abs(np.sin((xs*(1.3+i*.4)+i*.37)*np.pi))**1.5
        ridges.append((bases[i]-amps[i]*(0.6*dune+0.25*n))*H)
    for i,(ct,cb) in enumerate(P['land']):
        img=layer(img,ridges[i],ct,cb)
        if i==1:  # settlement on the second dune line
            sc=lerp(ct,P['land'][2][0],.55); lights=[]
            domes=[(.585,.016),(.61,.024),(.64,.013),(.675,.019),(.70,.011)]
            def draw(d,Pp,k):
                for x,r in domes:
                    gy=at(ridges[1],x)+.004; a,b=Pp(x-r*H/W,gy-r); c_,e=Pp(x+r*H/W,gy+r)
                    d.pieslice([a,b,c_,e],180,360,fill=rgba(sc,1))
                for x,ht in [(.625,.075),(.66,.045)]:
                    gy=at(ridges[1],x)+.004; a,b=Pp(x-.0012,gy-ht); c_,e=Pp(x+.0012,gy)
                    d.rectangle([a,b,c_,e],fill=rgba(sc,1)); a,b=Pp(x-.004,gy-ht*.8); c_,e=Pp(x+.004,gy-ht*.8+.004); d.ellipse([a,b,c_,e],fill=rgba(sc,1))
                a,b=Pp(.55,at(ridges[1],.55)-.003); c_,e=Pp(.72,at(ridges[1],.72)+.006)
            img2=vec(img,draw,.55,.75)
            for x,r in domes:
                gy=at(ridges[1],x)
                for j in range(3): lights.append((x+(j-1)*r*.35*H/W,gy-r*.35,1.6,P['warm'],P['lights']*.9))
            lights+= [(.625,at(ridges[1],.625)-.075,4,'#ff8a7a',P['lights']+.25),(.66,at(ridges[1],.66)-.045,3,P['warm'],P['lights'])]
            img=glows(img2,lights)
    # ships landing toward the settlement, each at its own stage
    def ships(d,Pp,k):
        for j,(x0,off,sz) in enumerate([(.63,0,1.4),(.66,.33,1.2),(.60,.66,1.1),(.69,.15,1.0)]):
            u=(p*3+off)%1; y=.10+u*(.56-.10); a=sm(0,.1,u)*sm(1,.85,u)
            craft(d,Pp,k,x0+(1-u)*.05*(j%2*2-1),y,90+ (j%2*2-1)*-8*(1-u),.08*(1-u*.5),a*.9,P['ship'],sz)
    img=vec(img,ships,0,.7)
    return img

# =============== TIDEWATER — calm sea, hydrofoil boats with wakes, gliders, moving sun & moon
TW={
 'dawn':dict(sky=[(0,'#3e4a7a'),(.4,'#9a90b8'),(.7,'#f0c3b8'),(1,'#f9e0cf')],blobs=[(.15,.68,.45,.12,'#ffd6b8',.6)],sun='#fff3ea',moon='#f4f0ff',st=.15,
   isl=['#b8a6bf','#8e7ea0','#5f5478'],sea=('#d8bcc0','#4a4870'),boat='#4a4468',ship='#ffffff',lights=.4,warm='#ffd9a8'),
 'day':dict(sky=[(0,'#3d7fb5'),(.5,'#88bfdc'),(.72,'#d4e8ec'),(1,'#e8f0ee')],blobs=[(.4,.2,.6,.3,'#9fd2ea',.3)],sun='#ffffff',moon='#ffffff',st=0,
   isl=['#a9c4cf','#7fa3b2','#4f7889'],sea=('#bcdbe2','#2f6a85'),boat='#f4f7f8',ship='#ffffff',lights=0,warm='#ffffff'),
 'sunset':dict(sky=[(0,'#2a2d5c'),(.35,'#7a4a7c'),(.6,'#e07f6d'),(.72,'#f8b77c'),(1,'#fbd59d')],blobs=[(.85,.7,.35,.1,'#ffc77a',.8)],sun='#ffe2b8',moon='#ffe9d0',st=.15,
   isl=['#c27b7a','#8a5170','#4f3256'],sea=('#f0a882','#2e2446'),boat='#3b2742',ship='#fff1e0',lights=.6,warm='#ffcf8a'),
 'night':dict(sky=[(0,'#070c22'),(.5,'#142048'),(.72,'#2a3a6a'),(1,'#344574')],blobs=[(.66,.35,.25,.25,'#3c5a95',.5)],sun='#ffffff',moon='#e8eeff',st=1.0,
   isl=['#2e3a62','#1f294b','#131a33'],sea=('#2a3a68','#060a1c'),boat='#0e1428',ship='#bfe3ff',lights=1,warm='#ffd08a'),
}
def boat(d,Pp,k,x,y,L,dirn,c,wake,wa):
    # sleek hydrofoil: long low wedge hull, swept cabin, thin foil struts
    px,py=Pp(x,y); l=L*W*2; h=l*.09; s=dirn
    for i in range(40):  # V-wake behind
        t=i/40; bx=px-s*l*.5-s*t*l*3.2; spread=t*l*.18
        a=wa*(1-t)**1.4
        d.line([(bx,py+h*.9+spread),(bx-s*l*.08,py+h*.9+spread*1.05)],fill=rgba(wake,a),width=max(1,int(k*1.2)))
        d.line([(bx,py+h*.9-spread*.25),(bx-s*l*.08,py+h*.9-spread*.26)],fill=rgba(wake,a*.6),width=max(1,int(k)))
    hull=[(px-s*l*.5,py),(px+s*l*.42,py),(px+s*l*.55,py-h*.55),(px-s*l*.3,py-h*.75),(px-s*l*.5,py-h*.5)]
    d.polygon(hull,fill=rgba(c,1))
    cab=[(px-s*l*.22,py-h*.7),(px+s*l*.12,py-h*.7),(px-s*l*.02,py-h*1.6),(px-s*l*.18,py-h*1.6)]
    d.polygon(cab,fill=rgba(c,1))
    d.line([(px-s*l*.3,py),(px-s*l*.28,py+h*.7)],fill=rgba(c,.9),width=max(1,int(k*1.3)))
    d.line([(px+s*l*.3,py),(px+s*l*.28,py+h*.7)],fill=rgba(c,.9),width=max(1,int(k*1.3)))
    d.line([(px-s*l*.36,py+h*.7),(px+s*l*.36,py+h*.7)],fill=rgba(c,.8),width=max(1,int(k)))
def tidewater(h):
    P=palette_at(TW,h); p=h/24; hz=.72
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,2,.65)
    sx,sy,sup=sun_pos(h,hz+.01,amp=.55); mx,my,mup=moon_pos(h,hz+.01,amp=.45)
    if sup: img=body(img,sx,sy,.03,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.026,P['moon'],.95,glow=.35,gc=P['moon'])
    # gliders in formation drifting across
    def fly(d,Pp,k):
        u=(p*2+.1)%1
        for j,(dx,dy) in enumerate([(0,0),(-.025,.022),(-.05,.044),(-.035,-.02)]):
            craft(d,Pp,k,.1+u*.8+dx,.45+dy+.04*math.sin(u*6),0,.05,.8*sm(0,.08,u)*sm(1,.92,u),P['ship'],1.2-j*.1)
    img=vec(img,fly,.3,.62)
    for i,c in enumerate(P['isl']):
        n=noise1d(xs,30+i,4,1.5+i)
        hill=np.exp(-((xs-[.15,.82,.05][i])/[.12,.10,.06][i])**2)+0.6*np.exp(-((xs-[.30,.95,.92][i])/[.06,.07,.08][i])**2)
        r=np.where(hill>0.02,(hz-(hill*[.06,.09,.13][i])*(1+.08*n))*H,H+5).astype(np.float32)
        img=layer(img,r,c,c)
    # lighthouse-beacon on the right island
    img=glows(img,[(.95,hz-.075,3.5,'#ff9a8a',P['lights']+.2),(.82,hz-.09,2,P['warm'],P['lights']*.8)])
    hpx=int(hz*H); below=H-hpx
    src=np.flipud(img[max(0,hpx-below):hpx]).copy()
    tt=np.linspace(0,1,below,dtype=np.float32)[:,None,None]
    base=mix(C(P['sea'][0]),C(P['sea'][1]),tt**.8); refl=mix(src,base,.35+.5*tt)
    r_=np.random.default_rng(5); rip=np.zeros((below,W),np.float32)
    for _ in range(int(800*max(S,.5))):
        y=int(r_.random()**1.5*below); x0=int(r_.random()*W); l=int((40+r_.random()*300*(1+y/below*3))*S)
        rip[y:y+max(1,int(2*S*(1+y/below))),x0:x0+l]+=.04*(1-y/below*.5)
    refl=refl+rip[...,None]; img[hpx:]=refl
    for (bx,up,c) in [(sx,sup,P['sun']),(mx,mup,P['moon'])]:
        if up:
            g=np.exp(-((X[hpx:]-bx*W)/(W*.02*(1+tt[...,0]*3)))**2)*np.clip(rip*12,0,1)
            img[hpx:]=mix(img[hpx:],C(c),g[...,None]*.85)
    # boats: positions advance through the day, perspective-scaled
    wake=lerp(P['sea'][0],'#ffffff',.5)
    boats=[(.80,.33,1,.021),(.86,.71,-1,.034),(.93,.05,1,.05)]
    def bdraw(d,Pp,k):
        for yy,off,dr_,L in boats:
            u=(p*1.5+off)%1; x=.1+u*.8 if dr_>0 else .9-u*.8
            boat(d,Pp,k,x,yy,L,dr_,P['boat'],wake,.55*sm(0,.06,u)*sm(1,.94,u))
    img=vec(img,bdraw,hz,1)
    lt=[]
    for yy,off,dr_,L in boats:
        u=(p*1.5+off)%1; x=.1+u*.8 if dr_>0 else .9-u*.8
        lt+=[(x+dr_*L*.5,yy-L*.0,1.5+L*60,'#9fe0ff',P['lights']),(x-dr_*L*.1,yy-L*1.2,1+L*40,P['warm'],P['lights']*.8)]
    return glows(img,lt)

# =============== MERIDIAN — snowy peaks, orbital ring, space-elevator tether with climber, observatories
MD={
 'dawn':dict(sky=[(0,'#3a3f74'),(.35,'#8a7fb0'),(.6,'#e6b3c0'),(1,'#f6dcd6')],blobs=[(.2,.6,.5,.15,'#ffd4c8',.5)],ring='#ffe6ee',ra=.7,sun='#fff0e8',moon='#f0f0ff',st=.25,
   mtn=[('#e9d3dc','#c9b3c9'),('#bca0bd','#937ca3'),('#7d6693','#594a75'),('#3f3560','#2a2445')],ship='#ffffff',lights=.4,warm='#ffe0b0'),
 'day':dict(sky=[(0,'#2f6ea8'),(.45,'#7fb3d8'),(.75,'#cfe3ef'),(1,'#eaf2f5')],blobs=[(.7,.2,.4,.3,'#aed6ef',.3)],ring='#ffffff',ra=.45,sun='#ffffff',moon='#ffffff',st=0,
   mtn=[('#e3edf3','#c4d6e2'),('#b7cbd9','#8ea8bd'),('#6f8ba3','#506d88'),('#34495f','#223345')],ship='#ffffff',lights=0,warm='#ffffff'),
 'sunset':dict(sky=[(0,'#262a5a'),(.35,'#6c4a86'),(.6,'#d9789a'),(.8,'#f5a98a'),(1,'#f8c79a')],blobs=[(.82,.62,.4,.15,'#ffbe8a',.6)],ring='#ffd2b0',ra=.75,sun='#ffe0b0',moon='#ffeedd',st=.25,
   mtn=[('#f0b6a8','#d89497'),('#b97a92','#8f5c80'),('#6a4473','#4b3260'),('#2e2243','#1d162e')],ship='#fff0e6',lights=.6,warm='#ffd08a'),
 'night':dict(sky=[(0,'#060a1e'),(.5,'#121a3e'),(.8,'#26305e'),(1,'#323a6a')],blobs=[(.4,.3,.5,.2,'#2f4f8a',.5),(.8,.15,.3,.2,'#3a7a8a',.3)],ring='#cdd8ff',ra=.8,sun='#ffffff',moon='#e6ecff',st=1.0,
   mtn=[('#5a668f','#47527a'),('#3c4670','#2e375c'),('#252d4d','#1b223c'),('#10152a','#0a0d1c')],ship='#d2e6ff',lights=1,warm='#ffd28a'),
}
def meridian(h):
    P=palette_at(MD,h); p=h/24; hz=.62
    img=sky(P['sky'],P['blobs']); img=starfield(img,P['st'],h,3,.6)
    sx,sy,sup=sun_pos(h,hz,amp=.5); mx,my,mup=moon_pos(h,hz,amp=.42)
    if sup: img=body(img,sx,sy,.028,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.022,P['moon'],.95,glow=.3,gc=P['moon'])
    def arc_y(x): return 1.25-1.05*math.sqrt(max(0,1-((x-.5)/.9)**2))
    d=np.sqrt(((X-W*.5)/(W*.9))**2+((Y-H*1.25)/(H*1.05))**2)
    for off,th,a in [(0,5,1),(.012,2.2,.6),(-.009,1.5,.4)]:
        m=np.clip((th*S-np.abs(d-1-off)*H*1.05)/1.5,0,1)*sm(0,.25,Xn)*sm(1,.75,Xn)*P['ra']*a
        img=mix(img,C(P['ring']),m[...,None])
    # tether from summit up to the ring, climber pod moving along it
    tx=.43; ty=arc_y(tx)
    bases=[.66,.74,.83,.93]; amps=[.20,.16,.10,.06]; ridges=[]
    for i in range(4):
        n=noise1d(xs,50+i,6,1.0+i*.5); pk=np.abs(noise1d(xs,60+i,3,.8+i*.4))
        ridges.append(((bases[i]-amps[i]*(.35+.25*n+.35*(1-pk/pk.max())**2))*H).astype(np.float32))
    gy=at(ridges[0],tx)
    cu=(p*4)%1; cy=gy-(gy-ty)*cu
    def teth(dd,Pp,k):
        a,b=Pp(tx,ty); c_,e=Pp(tx,gy); dd.line([a,c_],fill=rgba(P['ring'],.55*P['ra']+.15),width=max(1,int(k*1.2)))
        a,b=Pp(tx-.0018,cy-.006); c_,e=Pp(tx+.0018,cy+.006); dd.rounded_rectangle([a,b,c_,e],radius=k*2,fill=rgba(P['ring'],.95))
    img=vec(img,teth,ty-.01,gy+.01)
    img=glows(img,[(tx,cy,2.5,P['warm'],.3+P['lights']*.7),(tx,ty,4,P['ring'],.3+P['lights']*.5)])
    def fly(dd,Pp,k):
        for j,(x0,off,sz) in enumerate([(.30,0,1.5),(.33,.4,1.2),(.27,.7,1.1),(.62,.2,1.0),(.74,.55,.9)]):
            u=(p*3+off)%1; y=.55-u*.4
            craft(dd,Pp,k,x0+u*.03,y,-90+u*6,.09*(.6+u*.4),.85*sm(0,.1,u)*sm(1,.85,u),P['ship'],sz)
    img=vec(img,fly,.05,.62)
    for i,(ct,cb) in enumerate(P['mtn']):
        img=layer(img,ridges[i],ct,cb,depth=.35)
        if i==1:  # observatory domes on the second ridge
            sc=lerp(ct,P['mtn'][2][0],.4); obs=[(.58,.010),(.605,.007),(.20,.008)]
            def dr_(dd,Pp,k):
                for x,r in obs:
                    g=min(at(ridges[1],x-.006),at(ridges[1],x+.006))+.003
                    a,b=Pp(x-r*H/W,g-r); c_,e=Pp(x+r*H/W,g+r); dd.pieslice([a,b,c_,e],180,360,fill=rgba(sc,1))
                    a,b=Pp(x-r*H/W,g-.0005); c_,e=Pp(x+r*H/W,g+.012); dd.rectangle([a,b,c_,e],fill=rgba(sc,1))
                    a,b=Pp(x,g-r*.6); c_,e=Pp(x+r*1.4*H/W,g-r*1.3); dd.line([a,c_],fill=rgba(sc,1),width=int(k*3))
            img=vec(img,dr_,.35,.8)
            img=glows(img,[(x,min(at(ridges[1],x-.006),at(ridges[1],x+.006))+.008,1.8,P['warm'],P['lights']) for x,r in obs])
    return img

# =============== CANOPY — pine valley, spire, cabin lights, lantern drones, ships homing
CN={
 'dawn':dict(sky=[(0,'#4b4f80'),(.4,'#a39abd'),(.68,'#eec7c2'),(1,'#f6e3d6')],blobs=[(.2,.62,.4,.15,'#ffdcc0',.5),(.5,.15,.5,.15,'#2f7a7a',0)],st=.2,sun='#fff2e6',moon='#f2f2ff',
   hills=['#cbbacb','#a593b0'],trees=[('#7e6f95','#6c5f85'),('#55496f','#423a5c'),('#2f2742','#211b30')],spire='#9b8db0',light='#ffe9d8',ship='#ffffff',lights=.4,warm='#ffd9a0',aur=0),
 'day':dict(sky=[(0,'#4a8bbf'),(.45,'#93c4dc'),(.75,'#d9eadf'),(1,'#edf3e6')],blobs=[(.6,.25,.5,.3,'#b4dcea',.3),(.5,.15,.5,.15,'#2f7a7a',0)],st=0,sun='#ffffff',moon='#ffffff',
   hills=['#bcd3cc','#93b5ab'],trees=[('#6c9688','#5a8578'),('#3e6b60','#30574e'),('#1f3e37','#152c27')],spire='#8fb0b0',light='#ffffff',ship='#ffffff',lights=0,warm='#ffffff',aur=0),
 'sunset':dict(sky=[(0,'#2b2c5e'),(.35,'#714b80'),(.6,'#dd8070'),(.78,'#f6b47e'),(1,'#f9d39e')],blobs=[(.85,.64,.35,.12,'#ffc07c',.7),(.5,.15,.5,.15,'#2f7a7a',0)],st=.2,sun='#ffe0b0',moon='#ffeedd',
   hills=['#d9998a','#b57584'],trees=[('#8a5878','#734a6a'),('#4f3459','#3e2949'),('#251a32','#191223')],spire='#a2708a',light='#ffe2b0',ship='#fff0e0',lights=.6,warm='#ffc878',aur=0),
 'night':dict(sky=[(0,'#060b1f'),(.45,'#101c40'),(.75,'#1e3358'),(1,'#284262')],blobs=[(.2,.2,.3,.15,'#4a5aa0',.3),(.5,.15,.5,.15,'#2f7a7a',.35)],st=1.0,sun='#ffffff',moon='#eef2ff',
   hills=['#2c4560','#21364f'],trees=[('#1b2d45','#16253a'),('#111e31','#0d1726'),('#070d18','#04080f')],spire='#2b3f5c',light='#ffd38a',ship='#cfe6ff',lights=1,warm='#ffc070',aur=1),
}
def canopy(h):
    P=palette_at(CN,h); p=h/24
    img=sky(P['sky'],P['blobs'])
    if P['aur']>.02:  # slow aurora curtain, shifts with the hour
        a=P['aur']; wv=.16+.03*np.sin(Xn*7+h*.6)+.02*np.sin(Xn*17-h)
        band=np.exp(-((Yn-wv)/.05)**2)*(.75+.25*np.sin(Xn*9+h*.8))*np.exp(-((Xn-.5)/.45)**2)*a*.22
        img=mix(img,C('#5fe0b8'),band[...,None])
    img=starfield(img,P['st'],h,4,.6)
    hz=.64; sx,sy,sup=sun_pos(h,hz,amp=.5); mx,my,mup=moon_pos(h,hz,amp=.42)
    if sup: img=body(img,sx,sy,.026,P['sun'],1,glow=.6,gc=P['sun'])
    if mup: img=body(img,mx,my,.02,P['moon'],.95,glow=.3,gc=P['moon'])
    def fly(dd,Pp,k):
        u=(p*2+.3)%1
        for j,(dx,dy) in enumerate([(0,0),(.03,.03),(.055,-.01)]):
            craft(dd,Pp,k,.9-u*.75+dx,.36+dy+.05*u,180,.06,.8*sm(0,.08,u)*sm(1,.85,u),P['ship'],1.3-j*.15)
    img=vec(img,fly,.15,.6)
    for i,c in enumerate(P['hills']):
        img=layer(img,(([.62,.67][i]-.05*(.6+.4*noise1d(xs,70+i,3,1.0)))*H).astype(np.float32),c,c)
    sx_=.72; sw=np.clip(1-np.abs(Xn-sx_)/(.0035+.006*sm(.30,.62,Yn)),0,1)
    img=mix(img,C(P['spire']),(np.clip(sw*6,0,1)*(Yn>.30))[...,None])
    blink=.6+.4*math.cos(h*2.3)
    img=glows(img,[(sx_,.302,3,P['light'],.4+.6*P['lights']*blink),(sx_,.45,1.5,P['warm'],P['lights']*.7),(sx_,.55,1.5,P['warm'],P['lights']*.7)])
    rng=np.random.default_rng(11)
    for i,(ct,cb) in enumerate(P['trees']):
        base=[.70,.79,.91][i]; th=[.05,.085,.15][i]; per=[.010,.018,.032][i]
        r_=np.random.default_rng(80+i); k_=int(1/per)+2; hts=r_.uniform(.5,1,k_); jit=r_.uniform(-.3,.3,k_)
        idx=np.floor(xs/per).astype(int); frac=xs/per-idx
        tree=np.clip(hts[idx]*(1-np.abs(frac-.5-jit[idx]*.3)*2),0,None)
        r=((base-th*tree-th*.4*.4*noise1d(xs,90+i,3,1.0))*H).astype(np.float32)
        img=layer(img,r,ct,cb,depth=.2)
        if i==0:  # cabin windows glimmering between the far trees
            img=glows(img,[(x,base+.008,1.6,P['warm'],P['lights']*(.6+.4*rng.random())) for x in [.18,.185,.33,.47,.475,.58,.86,.865,.9]])
    # lantern drones: float above the trees from dusk to dawn, wandering slowly
    lt=[]
    for j in range(9):
        x=(.1+j*.1+.03*math.sin(h*.7+j*2))%1; y=.60+.06*math.sin(h*.5+j*1.3)+.02*j%3*.02
        lt.append((x,y,2.2,P['warm'],P['lights']*.9))
    return glows(img,lt)

THEMES={'Ringfall':ringfall,'Tidewater':tidewater,'Meridian':meridian,'Canopy':canopy}
HOURS=[0,4.5,5.5,6.25,7,8.5,10.5,12.5,14.5,16,17.25,18,18.75,19.5,20.5,22]

def run(j):
    n,i,hh,OUT=j; save(THEMES[n](hh),f'{OUT}/{n}_{i:02d}.png'); return n,i

if __name__=='__main__':
    from multiprocessing import Pool
    OUT=('out_port' if os.environ.get('PORTRAIT') else 'out16'+('_prev' if S<1 else '')); os.makedirs(OUT,exist_ok=True)
    sel=[a for a in sys.argv[1:] if not a.startswith('--')] or list(THEMES)
    jobs=[(n,i,hh,OUT) for n in sel for i,hh in enumerate(HOURS)]
    with Pool(int(os.environ.get('NP','4'))) as pl:
        for r in pl.imap_unordered(run,jobs): print(*r,flush=True)
