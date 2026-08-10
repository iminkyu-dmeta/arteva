## script 사용법
Camera-Info.py [cctv, extern, broadcast] --job [sel, add, del] --sid [100-107]
사용법 : sel : 조회, add: 추가, del: 삭제, act: 사용, sby: 미사용

## CCTV 등록 
# tp 시간 설정
python3 Camera-Info.py cctv --job add --sid 101 --evt tp --sti '00:00:00' --eti '05:00:00'
./Camera-Info.py cctv --job sel --sid 101

## EXTERN 등록 
./Camera-Info.py extern --job add --sid 101

## BROADCAST 등록 
./Camera-Info.py broadcast --job sel -sid 101
