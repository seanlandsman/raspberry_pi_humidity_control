
KEY=`cat adafruit.io.key.txt`

DATE=`date +%Y%m%d-%H%M`

adafruit-io client config --username seanlandsman --key $KEY
adafruit-io client groups get loft --json > ../data/Loft_$DATE.json
