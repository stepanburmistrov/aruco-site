import os
import cv2, cairosvg, numpy as np, pymupdf as fitz
from pathlib import Path
out = Path(os.environ.get('TEST_OUTPUT', 'work/charuco-check'))
for x,y,start in [(5,7,0),(6,8,10),(8,5,0),(2,2,0),(20,25,0)]:
 d=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
 board=cv2.aruco.CharucoBoard((x,y),35.,24.5,d,np.arange(start,start+x*y//2,dtype=np.int32))
 board.setLegacyPattern(False)
 expected=board.generateImage((x*200,y*200),marginSize=0,borderBits=1)
 svg=(out / f'board-{x}-{y}-{start}.svg').read_bytes()
 png=cairosvg.svg2png(bytestring=svg,output_width=x*200,output_height=y*200)
 actual=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_GRAYSCALE)
 # Ignore rasterization at rectangle edges, compare cell interiors.
 mismatch=np.mean((expected>127)!=(actual>127))
 assert mismatch<.015,(x,y,mismatch)
 ids=cv2.aruco.ArucoDetector(d).detectMarkers(actual)[1]
 assert ids is not None and sorted(ids.ravel())==list(range(start,start+x*y//2)),(x,y,ids)
 print(f'{x}x{y}, start {start}: all {len(ids)} markers detected; pixel difference {mismatch:.5%}')
for name in ['board','large','browser']:
 doc=fitz.open(out / f'{name}.pdf');page=doc[0];w,h=page.rect.width*25.4/72,page.rect.height*25.4/72
 assert len(doc)==1 and h>=w,(name,len(doc),w,h)
 if name!='large':assert abs(w-210)<.3 and abs(h-297)<.3
 pix=page.get_pixmap(matrix=fitz.Matrix(2,2),colorspace=fitz.csGRAY)
 img=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width)
 ids=cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)).detectMarkers(img)[1]
 assert ids is not None and len(ids)==17,(name,ids)
 print(name,'PDF:',w,h,'mm; 1 page; 17 markers detected')
