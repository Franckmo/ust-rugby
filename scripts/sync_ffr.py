#!/usr/bin/env python3
"""Collecte prudente des données publiques FFR : jamais de résultats supposés."""
import json, re, sys, datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = "https://monclubhouse.ffr.fr/competitions"
CATEGORIES = {"seniors": "federale-1", "espoirs": "espoirs-federaux"}
NAMES = {
 "US Tours":"Tours", "SC Royannais":"Saint-Jean-en-Royans",
 "US Montmelianaise":"Montmélian", "CS Nuiton":"Nuits-Saint-Georges",
 "US Issoirienne":"Issoire", "RC Auxerrois":"Auxerre",
 "Rugby Club de Courbevoie":"Courbevoie", "Beauvais XV RC":"Beauvais",
 "XV Corsaire Saint Malo Rugby":"Saint-Malo", "AS Bievre St Geoirs Rugby Club":"Bièvre Saint-Geoirs",
 "Paris Universite Club":"Paris UC", "US Annecy":"Annecy"
}
CLUBS = sorted(NAMES, key=len, reverse=True)
C = "(?:"+"|".join(re.escape(x) for x in CLUBS)+")"
GAME = re.compile(r"(\d{2}/\d{2}/20(?:26|27))\s+(\d{2}:\d{2})\s+("+C+r")\s+(?:(\d{1,3})\s*[-–]\s*(\d{1,3})\s+Terminé\s+)?("+C+r")")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 (compatible; USTRugbyStatus/1.0; contact: repository Franckmo/ust-rugby)"})
def get(url):
 r=SESSION.get(url,timeout=35)
 r.raise_for_status()
 if len(r.content)<3000: raise RuntimeError("Page FFR incomplète")
 return BeautifulSoup(r.text,"html.parser")
def collect_games(html):
 # Les pages publiques affichent toutes les journées et la mention « Terminé » pour les résultats validés.
 text=" ".join(html.stripped_strings)
 text=re.sub(r"\s+"," ",text)
 matches={}
 for m in GAME.finditer(text):
  date,hour,home,hs,aw,away=m.groups()
  iso=datetime.datetime.strptime(date+" "+hour,"%d/%m/%Y %H:%M").isoformat(timespec="minutes")
  if home!="US Tours" and away!="US Tours": continue
  game={"date":iso[:10],"time":hour,"home":NAMES[home],"away":NAMES[away],"status":"finished" if hs is not None else "scheduled"}
  if hs is not None: game.update({"homeScore":int(hs),"awayScore":int(aw)})
  matches[(iso,home,away)]=game
 return sorted(matches.values(),key=lambda x:(x["date"],x["time"]))
def collect_standings(html):
 rows=[]
 for tr in html.find_all("tr"):
  cells=[" ".join(td.stripped_strings) for td in tr.find_all(["td","th"],recursive=False)]
  club=next((NAMES[n] for cell in cells for n in CLUBS if cell==n),None)
  if not club: continue
  idx=next((i for i,t in enumerate(cells) if t in NAMES),None)
  if idx is None: continue
  # La structure officielle est Rang, Club, PTS, J, ...
  nums=[]
  for t in cells[idx+1:]:
   if re.fullmatch(r"\d{1,3}",t): nums.append(int(t))
  if len(nums)>=2: rows.append({"club":club,"points":nums[0],"played":nums[1]})
 # Refuser les tableaux partiels ou les classements de saison précédente.
 if len({r["club"] for r in rows})!=12 or not any(r["club"]=="Tours" for r in rows): return []
 return rows
def main():
 dest=Path("ffr-data.json")
 old={}
 if dest.exists():
  try: old=json.loads(dest.read_text(encoding="utf8"))
  except (OSError,ValueError): pass
 out={"source":"FFR Mon Club House","lastChecked":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),"teams":{}}
 errors=[]
 for team,slug in CATEGORIES.items():
  previous=old.get("teams",{}).get(team,{})
  group=dict(previous)
  try:
   games=collect_games(get(f"{ROOT}/{slug}/calendrier-resultats"))
   # Protection : ne pas remplacer des résultats fiables par une page vide/partielle.
   if len(games)<7 or len([x for x in games if x["status"]=="finished"])<3:
    raise ValueError(f"Calendrier incomplet : {len(games)} matchs")
   prior={(x["date"],x["home"],x["away"]):x for x in previous.get("games",[])}
   for g in games:
    key=(g["date"],g["home"],g["away"])
    if g["status"]!="finished" and prior.get(key,{}).get("status")=="finished":
     g=prior[key]
    prior[key]=g
   group["games"]=sorted(prior.values(),key=lambda x:(x["date"],x.get("time","")))
   group["gamesUpdatedAt"]=out["lastChecked"]
  except Exception as exc: errors.append(f"{team} calendrier: {exc}")
  try:
   ranking=collect_standings(get(f"{ROOT}/{slug}/classements"))
   if not ranking: raise ValueError("Classement incomplet (attendu 12 équipes)")
   group["standings"]=ranking
   group["standingsUpdatedAt"]=out["lastChecked"]
  except Exception as exc: errors.append(f"{team} classement: {exc}")
  out["teams"][team]=group
 # Ne pas écrire un fichier vide ou un état qui dégrade les données existantes.
 usable=all(t.get("games") or t.get("standings") for t in out["teams"].values())
 if not usable:
  print("Echec : aucune donnée fiable complète par équipe",file=sys.stderr)
  for e in errors: print(e,file=sys.stderr)
  sys.exit(1)
 dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 for e in errors: print("AVERTISSEMENT : "+e)
 print("Collecte terminée :",*[f"{k} {len(v.get('games',[]))} matchs, {len(v.get('standings',[]))} clubs" for k,v in out["teams"].items()])
if __name__=="__main__": main()
