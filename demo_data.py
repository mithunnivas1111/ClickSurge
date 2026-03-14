"""
Demo Data Generator — Realistic SEO Data with proper CTR-Position correlation

Real Google CTR curve (industry average):
  Position 1   → 28–35% CTR
  Position 2   → 15–20%
  Position 3   → 10–13%
  Position 4–6 → 5–8%
  Position 7–10→ 2–4%
  Position 11–20→ 0.5–2%
  Position 20+ → 0.1–0.5%
"""
import pandas as pd
import random

random.seed(42)

# ── URL pools ──
BRANDS = ['nike','adidas','puma','reebok','asics','new-balance','under-armour',
          'saucony','brooks','hoka','salomon','mizuno','on-running','altra','vans']
CATEGORIES = ['running-shoes','trail-shoes','basketball-shoes','tennis-shoes',
              'walking-shoes','gym-shoes','casual-shoes','hiking-boots',
              'cycling-shoes','cross-training','yoga','football-boots',
              'cricket-shoes','badminton-shoes','swimming']
BLOG_TOPICS = [
    'best-running-shoes-2024','how-to-choose-running-shoes','nike-vs-adidas',
    'top-trail-shoes-review','cushioning-guide-2024','marathon-training-gear',
    'shoe-size-guide','running-form-tips','injury-prevention-guide',
    'best-budget-running-shoes','carbon-plate-shoes-review','stability-vs-neutral',
    'running-shoes-for-flat-feet','best-shoes-for-overpronation',
    'how-to-break-in-new-shoes','best-adidas-shoes-2024','nike-air-max-history',
    'asics-gel-vs-foam','brooks-ghost-review','hoka-one-one-review',
    'best-shoes-for-marathon','ultra-running-gear-guide','track-vs-road-shoes',
    'waterproof-running-shoes','minimalist-shoes-guide',
]
SALE_PAGES       = ['clearance','new-arrivals','mid-season-sale','flash-sale',
                    'bundle-deals','student-discount','loyalty-rewards','outlet']
COLLECTION_PAGES = ['mens-running','womens-running','kids-shoes','wide-fit',
                    'vegan-shoes','eco-friendly','limited-edition','collab-drops']


def make_url(i):
    pool = len(CATEGORIES)+len(BRANDS)+len(BLOG_TOPICS)+len(SALE_PAGES)+len(COLLECTION_PAGES)
    if i < len(CATEGORIES):
        return f'https://demo-store.com/category/{CATEGORIES[i]}'
    elif i < len(CATEGORIES)+len(BRANDS):
        return f'https://demo-store.com/brands/{BRANDS[i-len(CATEGORIES)]}'
    elif i < len(CATEGORIES)+len(BRANDS)+len(BLOG_TOPICS):
        return f'https://demo-store.com/blog/{BLOG_TOPICS[i-len(CATEGORIES)-len(BRANDS)]}'
    elif i < len(CATEGORIES)+len(BRANDS)+len(BLOG_TOPICS)+len(SALE_PAGES):
        return f'https://demo-store.com/sale/{SALE_PAGES[i-len(CATEGORIES)-len(BRANDS)-len(BLOG_TOPICS)]}'
    elif i < pool:
        idx = i-len(CATEGORIES)-len(BRANDS)-len(BLOG_TOPICS)-len(SALE_PAGES)
        return f'https://demo-store.com/collection/{COLLECTION_PAGES[idx]}'
    else:
        return f'https://demo-store.com/product/{BRANDS[i%len(BRANDS)]}-{CATEGORIES[i%len(CATEGORIES)]}-{i}'


def realistic_ctr(position, page_type):
    """
    Generate CTR that MATCHES the position using Google's real CTR curve.
    Adds small random variation around the expected value.
    """
    # Base CTR curve by position (Google industry averages)
    if position <= 1:
        base = random.uniform(0.28, 0.36)
    elif position <= 2:
        base = random.uniform(0.15, 0.22)
    elif position <= 3:
        base = random.uniform(0.10, 0.14)
    elif position <= 4:
        base = random.uniform(0.07, 0.10)
    elif position <= 5:
        base = random.uniform(0.05, 0.08)
    elif position <= 6:
        base = random.uniform(0.04, 0.07)
    elif position <= 7:
        base = random.uniform(0.03, 0.05)
    elif position <= 8:
        base = random.uniform(0.025, 0.045)
    elif position <= 10:
        base = random.uniform(0.018, 0.035)
    elif position <= 12:
        base = random.uniform(0.010, 0.022)
    elif position <= 15:
        base = random.uniform(0.007, 0.015)
    elif position <= 20:
        base = random.uniform(0.004, 0.010)
    elif position <= 30:
        base = random.uniform(0.002, 0.006)
    else:
        base = random.uniform(0.001, 0.003)

    # Intentionally bad CTR for low_ctr pages (the SEO opportunity)
    if page_type == 'low_ctr':
        base = base * random.uniform(0.15, 0.35)   # 65–85% below expected

    # Slightly above average for star pages (great title/meta)
    elif page_type == 'star':
        base = base * random.uniform(1.1, 1.4)

    return min(round(base, 6), 0.99)


def generate_demo_page_data(num_pages=50):
    """
    Generate realistic page-level data.

    Page type distribution modelled on a real mid-size e-commerce site:
      star        12% — Top positions, high traffic, great CTR
      normal      25% — Healthy average pages
      low_ctr     15% — High position but poor CTR (SEO opportunity)
      low_hanging 13% — Positions 8-12, almost page 1
      page2_trap  10% — Positions 11-15, high impressions
      declining   10% — Slipping rankings
      new_page    10% — New content building up
      zero_clicks  5% — Shows in search, zero engagement
    """
    page_types = ['star','normal','low_ctr','low_hanging','page2_trap','declining','new_page','zero_clicks']
    weights    = [0.12,  0.25,   0.15,    0.13,         0.10,        0.10,       0.10,      0.05]

    pages = []
    for i in range(num_pages):
        url   = make_url(i)
        ptype = random.choices(page_types, weights=weights, k=1)[0]

        # ── Position first, then derive CTR from it ──
        if ptype == 'star':
            impressions = random.randint(15000, 80000)
            position    = random.uniform(1.0, 3.5)

        elif ptype == 'normal':
            impressions = random.randint(500, 12000)
            position    = random.uniform(3.0, 10.0)

        elif ptype == 'low_ctr':
            impressions = random.randint(3000, 50000)
            position    = random.uniform(1.5, 8.0)

        elif ptype == 'low_hanging':
            impressions = random.randint(2000, 25000)
            position    = random.uniform(8.0, 12.0)

        elif ptype == 'page2_trap':
            impressions = random.randint(1500, 20000)
            position    = random.uniform(11.0, 15.0)

        elif ptype == 'declining':
            impressions = random.randint(1000, 10000)
            position    = random.uniform(6.0, 15.0)

        elif ptype == 'new_page':
            impressions = random.randint(50, 1500)
            position    = random.uniform(12.0, 35.0)

        else:  # zero_clicks
            impressions = random.randint(1000, 8000)
            position    = random.uniform(8.0, 25.0)

        # CTR derived from position (realistic correlation)
        ctr    = realistic_ctr(position, ptype)
        clicks = max(0, int(impressions * ctr))

        # Override for zero_clicks — force near-zero clicks
        if ptype == 'zero_clicks':
            clicks = random.randint(0, 4)
            ctr    = round(clicks / impressions if impressions > 0 else 0, 6)

        pages.append({
            'page':        url,
            'impressions': impressions,
            'clicks':      clicks,
            'ctr':         ctr,
            'position':    round(position, 2),
            'page_type':   ptype,
        })

    df = pd.DataFrame(pages)
    df = df.sort_values('impressions', ascending=False).reset_index(drop=True)
    return df


def generate_demo_query_data(num_queries=200):
    keyword_seeds = [
        'best running shoes','nike running shoes','running shoes for men',
        'running shoes for women','cheap running shoes','running shoes sale',
        'best running shoes 2024','lightweight running shoes','cushioned running shoes',
        'trail running shoes','marathon shoes','nike air max','adidas ultraboost',
        'brooks ghost 15','hoka clifton 9','asics gel nimbus','new balance 1080',
        'running shoes flat feet','running shoes overpronation','waterproof running shoes',
        'running shoes wide fit','vegan running shoes','carbon plate running shoes',
        'stability running shoes','neutral running shoes','minimalist running shoes',
        'buy running shoes online','running shoes discount','running shoes near me',
        'best budget running shoes',
    ]
    queries = []
    for i in range(num_queries):
        query = keyword_seeds[i] if i < len(keyword_seeds) else \
            f'{random.choice(BRANDS)} {random.choice(CATEGORIES).replace("-"," ")} {random.choice(["review","buy","2024","sale","mens","womens"])}'
        position    = random.uniform(1.0, 25.0)
        impressions = random.randint(200, 40000)
        ctr         = realistic_ctr(position, 'normal')
        clicks      = int(impressions * ctr)
        queries.append({
            'query': query, 'impressions': impressions,
            'clicks': clicks, 'ctr': round(ctr, 6), 'position': round(position, 2),
        })
    df = pd.DataFrame(queries)
    return df.sort_values('impressions', ascending=False).reset_index(drop=True)


def generate_demo_page_query_data():
    data = []
    scenarios = [
        ('best running shoes', [
            'https://demo-store.com/blog/best-running-shoes-2024',
            'https://demo-store.com/category/running-shoes',
            'https://demo-store.com/collection/mens-running',
            'https://demo-store.com/sale/new-arrivals',
        ]),
        ('nike running shoes', [
            'https://demo-store.com/brands/nike',
            'https://demo-store.com/category/running-shoes',
            'https://demo-store.com/blog/nike-vs-adidas',
        ]),
        ('trail running shoes', [
            'https://demo-store.com/category/trail-shoes',
            'https://demo-store.com/blog/top-trail-shoes-review',
            'https://demo-store.com/brands/salomon',
        ]),
        ('adidas running shoes', [
            'https://demo-store.com/brands/adidas',
            'https://demo-store.com/blog/nike-vs-adidas',
        ]),
        ('cheap running shoes', [
            'https://demo-store.com/sale/clearance',
            'https://demo-store.com/blog/best-budget-running-shoes',
            'https://demo-store.com/sale/flash-sale',
        ]),
    ]
    for query, pages in scenarios:
        for page in pages:
            pos = round(random.uniform(3.5, 10.0), 2)
            imp = random.randint(2000, 8000)
            ctr = realistic_ctr(pos, 'normal')
            data.append({
                'page': page, 'query': query,
                'impressions': imp, 'clicks': int(imp * ctr),
                'position': pos,
            })
    normal = [
        ('https://demo-store.com/blog/how-to-choose-running-shoes', 'how to choose running shoes', 4500, 2.8),
        ('https://demo-store.com/category/hiking-boots',            'hiking boots online',          3200, 4.1),
        ('https://demo-store.com/blog/marathon-training-gear',      'marathon gear guide',           2800, 3.5),
        ('https://demo-store.com/collection/womens-running',        'womens running shoes',          5500, 3.2),
        ('https://demo-store.com/category/basketball-shoes',        'basketball shoes buy',          4100, 4.8),
        ('https://demo-store.com/brands/hoka',                      'hoka running shoes',            6200, 3.1),
        ('https://demo-store.com/brands/brooks',                    'brooks running shoes',          4800, 3.7),
        ('https://demo-store.com/sale/student-discount',            'student shoe discount',         2100, 5.2),
    ]
    for page, query, imp, pos in normal:
        ctr = realistic_ctr(pos, 'normal')
        data.append({'page': page, 'query': query, 'impressions': imp,
                     'clicks': int(imp * ctr), 'position': pos})
    df = pd.DataFrame(data)
    df['ctr'] = (df['clicks'] / df['impressions']).round(6)
    return df


def save_demo_data():
    print("Generating realistic demo Search Console data...")
    page_data       = generate_demo_page_data(1000)
    query_data      = generate_demo_query_data(200)
    page_query_data = generate_demo_page_query_data()

    page_data.to_csv('demo_page_data.csv',            index=False)
    query_data.to_csv('demo_query_data.csv',           index=False)
    page_query_data.to_csv('demo_page_query_data.csv', index=False)

    print(f"✅ {len(page_data)} pages  |  {len(query_data)} queries  |  {len(page_query_data)} page-query pairs")
    print(f"\nPosition  — avg: {page_data['position'].mean():.1f}  |  range: {page_data['position'].min():.1f}–{page_data['position'].max():.1f}")
    print(f"CTR       — avg: {page_data['ctr'].mean():.2%}  |  range: {page_data['ctr'].min():.2%}–{page_data['ctr'].max():.2%}")
    print(f"Impressions — avg: {page_data['impressions'].mean():,.0f}  |  max: {page_data['impressions'].max():,}")
    print(f"\nPage type split:")
    print(page_data['page_type'].value_counts().to_string())


if __name__ == "__main__":
    save_demo_data()