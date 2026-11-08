#!/usr/bin/env python3
"""Collecte prudente des données publiques FFR : jamais de résultats supposés."""
import json, re, sys, datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = "https://monclubhouse.ffr.fr"
CATEGORIES = {"seniors": "nationales/federale-1", "espoirs": "competitions/espoirs-federaux"}
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
GAME = re.compile(r"(\d{2}/\d{2}/20(?:26|27))\s+(\d{2}:\d{2})\s+("+C+r")\s+(?:(\d{1,3})\s*[-–]\s*(\d{1,3})\s+(Terminé|En cours|Mi-temps|En direct)\s+)?("+C+r")")
def get(browser,url):
 page=browser.new_page(locale="fr-FR")
 try:
  page.goto(url,wait_until="domcontentloaded",timeout=45000)
  page.wait_for_timeout(2500)
  # Le site FFR hydrate ses compétitions côté navigateur.
  for attempt in range(5):
   content=page.content()
   if "US Tours" in content and ("Journée" in content or "PTS" in content):
    return BeautifulSoup(content,"html.parser")
   page.wait_for_timeout(1500)
  raise RuntimeError("La FFR n'a pas chargé les données du championnat")
 finally:
  page.close()
def collect_live(browser):
 page=browser.new_page(locale="fr-FR")
 try:
  page.goto(ROOT+"/rugby-direct",wait_until="domcontentloaded",timeout=45000)
  page.wait_for_timeout(1500)
  try:page.get_by_text("Tous les matchs",exact=True).first.click(timeout=6000)
  except Exception as e:print("onglet absent",str(e)[:150])
  page.wait_for_timeout(2000)
  try: page.get_by_text("Compétitions Nationales",exact=True).first.click(timeout=4000)
  except Exception as e: print("nationales click",str(e)[:100])
  page.wait_for_timeout(1000)
  try: page.get_by_text("Fédérale 1",exact=True).first.click(timeout=4000)
  except Exception as e: print("F1 click",str(e)[:100])
  page.wait_for_timeout(2500)
  text=" ".join(page.locator("body").inner_text().split())
  ix=text.find("US Tours")
  print("LIVE DIAGNOSTIC: len",len(text),"Tours position",ix,"snippet",text[max(0,ix-450):ix+650] if ix>=0 else text[:1200])
  return []
 finally:
  page.close()

def collect_games(html):
 # Les pages publiques affichent toutes les journées et la mention « Terminé » pour les résultats validés.
 text=" ".join(html.stripped_strings)
 text=re.sub(r"\s+"," ",text)
 matches={}
 for m in GAME.finditer(text):
  date,hour,home,hs,aw,match_status,away=m.groups()
  iso=datetime.datetime.strptime(date+" "+hour,"%d/%m/%Y %H:%M").isoformat(timespec="minutes")
  if home!="US Tours" and away!="US Tours": continue
  game={"date":iso[:10],"time":hour,"home":NAMES[home],"away":NAMES[away],"status":("finished" if match_status=="Terminé" else "live" if match_status in ("En cours","Mi-temps","En direct") else "scheduled")}
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
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True)
  try: collect_live(browser)
  except Exception as exc:print('DIRECT non accessible:',str(exc))
  for team,slug in CATEGORIES.items():
   previous=old.get("teams",{}).get(team,{})
   group=dict(previous)
   try:
    games=collect_games(get(browser,f"{ROOT}/{slug}/calendrier-resultats"))
    # Chaque source doit fournir suffisamment de rencontres et de résultats vérifiés.
    if len(games)<7 or len([x for x in games if x["status"]=="finished"])<3:
     raise ValueError(f"Calendrier incomplet : {len(games)} matchs")
    prior={(x["date"],x["home"],x["away"]):x for x in previous.get("games",[])}
    for g in games:
     key=(g["date"],g["home"],g["away"])
     if g["status"]!="finished" and prior.get(key,{}).get("status")=="finished":g=prior[key]
     prior[key]=g
    group["games"]=sorted(prior.values(),key=lambda x:(x["date"],x.get("time","")))
    group["gamesUpdatedAt"]=out["lastChecked"]
   except Exception as exc:errors.append(f"{team} calendrier: {exc}")
   try:
    ranking=collect_standings(get(browser,f"{ROOT}/{slug}/classements"))
    if not ranking:raise ValueError("Classement incomplet (attendu 12 équipes)")
    prior_played=next((x["played"] for x in previous.get("standings",[]) if x["club"]=="Tours"),0)
    new_played=next((x["played"] for x in ranking if x["club"]=="Tours"),0)
    if new_played<prior_played:raise ValueError("Classement plus ancien que le dernier connu")
    group["standings"]=ranking
    group["standingsUpdatedAt"]=out["lastChecked"]
   except Exception as exc:errors.append(f"{team} classement: {exc}")
   out["teams"][team]=group
  browser.close()
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
