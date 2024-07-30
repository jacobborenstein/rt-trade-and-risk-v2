import time
from fastapi import FastAPI, Request
import redis
import price_scraper
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
tickers = 'MMM ACE ABT ANF ACN ADBE AMD AES AET AFL A GAS APD ARG AKAM AA ALXN ATI AGN ALL ANR ALTR MO AMZN AEE AEP AXP AIG AMT AMP ABC AMGN APH APC ADI AON APA AIV APOL AAPL AMAT ADM AIZ T ADSK ADP AN AZO AVB AVY AVP BHI BLL BAC BK BCR BAX BBT BEAM BDX BBBY BMS BRK.B BBY BIG BIIB BLK HRB BMC BA BWA BXP BSX BMY BRCM BF.B CHRW CA CVC COG CAM CPB COF CAH CFN KMX CCL CAT CBG CBS CELG CNP CTL CERN CF SCHW CHK CVX CMG CB CI CINF CTAS CSCO C CTXS CLF CLX CME CMS COH KO CCE CTSH CL CMCSA CMA CSC CAG COP CNX ED STZ CBE GLW COST CVH COV CCI CSX CMI CVS DHI DHR DRI DVA DF DE DELL DNR XRAY DVN DV DO DTV DFS DISCA DLTR D RRD DOV DOW DPS DTE DD DUK DNB ETFC EMN ETN EBAY ECL EIX EW EA EMC EMR ESV ETR EOG EQT EFX EQR EL EXC EXPE EXPD ESRX XOM FFIV FDO FAST FII FDX FIS FITB FHN FSLR FE FISV FLIR FLS FLR FMC FTI F FRX FOSL BEN FCX FTR GME GCI GPS GD GE GIS GPC GNW GILD GS GT GOOG GWW HAL HOG HAR HRS HIG HAS HCP HCN HNZ HP HES HPQ HD HON HRL HSP HST HCBK HUM HBAN ITW IR TEG INTC ICE IBM IFF IGT IP IPG INTU ISRG IVZ IRM JBL JEC JDSU JNJ JCI JOY JPM JNPR K KEY KMB KIM KMI KLAC KSS KFT KR LLL LH LRCX LM LEG LEN LUK LXK LIFE LLY LTD LNC LLTC LMT L LO LOW LSI MTB M MRO MPC MAR MMC MAS MA MAT MKC MCD MHP MCK MJN MWV MDT MRK MET PCS MCHP MU MSFT MOLX TAP MON MNST MCO MS MOS MSI MUR MYL NBR NDAQ NOV NTAP NFLX NWL NFX NEM NWSA NEE NKE NI NE NBL JWN NSC NTRS NOC NU NRG NUE NVDA NYX ORLY OXY OMC OKE ORCL OI PCAR PLL PH PDCO PAYX BTU JCP PBCT POM PEP PKI PRGO PFE PCG PM PSX PNW PXD PBI PCL PNC RL PPG PPL PX PCP PCLN PFG PG PGR PLD PRU PEG PSA PHM QEP PWR QCOM DGX RRC RTN RHT RF RSG RAI RHI ROK COL ROP ROST RDC R SWY SAI CRM SNDK SCG SLB SNI STX SEE SHLD SRE SHW SIAL SPG SLM SJM SNA SO LUV SWN SE S STJ SWK SPLS SBUX HOT STT SRCL SYK SUN STI SYMC SYY TROW TGT TEL TE THC TDC TER TSO TXN TXT HSY TRV TMO TIF TWX TWC TIE TJX TMK TSS TRIP TSN TYC USB UNP UNH UPS X UTX UNM URBN VFC VLO VAR VTR VRSN VZ VIAB V VNO VMC WMT WAG DIS WPO WM WAT WPI WLP WFC WDC WU WY WHR WFM WMB WIN WEC WPX WYN WYNN XEL XRX XLNX XL XYL YHOO YUM ZMH ZION'
ticker_list = tickers.split(" ")
r = redis.Redis(host='localhost', port=6379)
r.ping()
client = 0
while True:
    for t in ticker_list:
        data = price_scraper.get_with_data(t, client)
        print(client)
        client += 1
        client = client % 5
        sendable = json.dumps(data)
        r.publish(t, sendable)
        r.publish('prices_and_values', sendable)
        logger.info("status: Sent " + str(data))
        time.sleep(.4)