from secrets import CLIENT_ID, CLIENT_SECRET, USERID, ACCESS_TOKEN
from datetime import datetime
import requests
import operator
import json

def get_data():
    dt = datetime(2017, 1, 1, 0, 0)
    timestamp = int(dt.timestamp())

    json_file = 'data/foursqure-checkins.json'

    # api endpoint to download your checkin history
    url = "https://api.foursquare.com/v2/users/self/checkins"

    params = dict(
      client_id=CLIENT_ID,
      client_secret=CLIENT_SECRET,
      oauth_token=ACCESS_TOKEN,
      limit=250,
      offset=0,
      v='20170801',
      afterTimestamp=timestamp
    )

    data = []
    items = []
    while True:
        print(params['offset'], end=' ')
        response = requests.get(url, params=params)
        if len(response.json()['response']['checkins']['items']) == 0:
            items += response.json()['response']['checkins']['items']
            break #whenever api returns no rows, offset value has exceeded total records so we're done
        data += response.json()['response']['checkins']['items']
        params['offset'] += 250

    # Back up to a file
    with open(json_file, 'w') as f:
        f.write(json.dumps(data, indent=2))
    return data

def sort_data(items):
    # Find the number checkins for different categories
    cats = []
    for c in items:
        cats += [cat['id'] for cat in c['venue']['categories']]
    cats = set(cats)
    cat_dist = {c: 0 for c in cats}
    for c in items:
        for cat in c['venue']['categories']:
            cat_dist[cat['id']] += 1

    # Number of checkins for venue
    venues = set([c['venue']['id'] for c in items])
    venue_dist = {v:0 for v in venues}

    for item in items:
        venue_dist[item['venue']['id']] += 1

    # Unique countries
    countries = set([item['venue']['location']['country'] for item in items])
    # states = set([item['venue']['location']['state'] for item in items])

    sorted_venue = sorted(venue_dist.items(), key=operator.itemgetter(1),reverse=True)

    return cat_dist, sorted_venue, countries

def create_venue_dict(items):
    venues = {}
    for item in items:
        if not venues.get(item['venue']['id'], None):
            venues[item['venue']['id']] = item['venue']
    return venues

def create_geojson_checkins(venues, venue_checkins):
    geos = []
    for k, v in venue_checkins.items():
        venue = {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [ v['location']['lng'],v['location']['lat']]
          },
          "properties": {
            "name": v['name'],
            "visits": venues[k],
            "country":v['location']['country'],
            "place":v['location'].get('crossStreet','')
          }
        }
        geos.append(venue)
    geos_dict = {
      "type": "FeatureCollection",
      "metadata": {
        "generated": 1395197681000,
        "url": "http://www.yearzero.uk",
        "title": "Year Zero checkins",
        "status": 200,
        "api": "1.0.13",
        "count": len(geos)
      },
      "features": geos
      }
    return geos_dict

def get_categories():
    '''
    Call API to get categories from foursquare
    '''
    url = 'https://api.foursquare.com/v2/venues/categories'
    params = {'oauth_token':ACCESS_TOKEN, 'v':'20170801'}
    r = requests.get(url, params=params)
    cat_names = expand_categories(r.json())

    # Back up to a file
    with open('data/foursqure-categories.json', 'w') as f:
        f.write(json.dumps(cat_names, indent=2))

    return cat_names

def import_categories():
    with open('data/foursqure-categories.json', 'r') as f:
        categories = json.load(f)

    return categories

def import_data():
    with open('data/foursqure-checkins.json', 'r') as f:
        checkins = json.load(f)

    return checkins

def expand_categories(categories):
    cats_names = {}
    for category in categories['response']['categories']:
         cats_names[category['id']]= category['name']
         for cat in category['categories']:
             cats_names[cat['id']]= cat['name']
             for c in cat['categories']:
                 cats_names[c['id']]= c['name']
                 for ca in c['categories']:
                     cats_names[ca['id']]= ca['name']
    return cats_names

def translate_categories(cat_dist, cat_names):
    cat_results = {}
    for k, v in cat_dist.items():
        try:
            cat_results[cat_names[k]] = v
        except:
            print("NO MATCH for {}".format(k))
    sorted_cats = sorted(cat_results.items(), key=operator.itemgetter(1),reverse=True)
    return sorted_cats

def main():
    items = import_data()
    cat_names = import_categories()
    cat_dist, venue_dist, countries = sort_data(items)
    results = translate_categories(cat_dist, cat_names)
    return results, venue_dist

if __name__ == '__main__':
    results, venue_dist = main()
    print(results[0:20], venue_dist[0:20])
