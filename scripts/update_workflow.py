#!/usr/bin/env python3
"""Update the workflow.json with new Fetch All Campaign Data code."""
import json
import os

WORKFLOW_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflow.json')

with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
    wf = json.load(f)

# Find the "Fetch All Campaign Data" node
for node in wf['nodes']:
    if node['name'] == 'Fetch All Campaign Data':
        node['parameters']['jsCode'] = r'''const campaignIds = $input.first().json.campaignIds;
const token = $env.LINKEDIN_ACCESS_TOKEN;
const accountId = $env.LINKEDIN_ACCOUNT_ID;

const restHeaders = {
  'Authorization': `Bearer ${token}`,
  'LinkedIn-Version': '202503',
  'X-Restli-Protocol-Version': '2.0.0'
};
const v2Headers = {
  'Authorization': `Bearer ${token}`,
  'X-Restli-Protocol-Version': '2.0.0'
};

const GEO_MAP = {
  'urn:li:geo:103644278': 'US', 'urn:li:geo:101174742': 'Canada',
  'urn:li:geo:102713980': 'India', 'urn:li:geo:104305776': 'UAE',
  'urn:li:geo:102890719': 'UK', 'urn:li:geo:101282230': 'Germany',
  'urn:li:geo:100961908': 'Australia',
  'urn:li:geo:102956297': 'Mumbai', 'urn:li:geo:106164952': 'Mumbai',
  'urn:li:geo:108393811': 'Navi Mumbai', 'urn:li:geo:101389470': 'Indore'
};

function resolveGeo(geoUrns) {
  if (!geoUrns?.length) return 'Global';
  const names = [...new Set(geoUrns.map(u => GEO_MAP[u] || u.split(':').pop()))];
  if (names.includes('US') && names.includes('Canada') && names.length === 2) return 'US, Canada';
  return names.join(', ');
}

const PIVOTS = ['MEMBER_COMPANY','MEMBER_SENIORITY','MEMBER_INDUSTRY','MEMBER_COMPANY_SIZE','MEMBER_JOB_FUNCTION','MEMBER_JOB_TITLE','MEMBER_REGION_V2','MEMBER_COUNTRY_V2'];
const SENIORITY_MAP = {'urn:li:seniority:10':'Owner','urn:li:seniority:9':'Partner','urn:li:seniority:8':'Owner','urn:li:seniority:7':'Partner','urn:li:seniority:6':'CXO','urn:li:seniority:5':'VP','urn:li:seniority:4':'Director','urn:li:seniority:3':'Manager','urn:li:seniority:2':'Senior','urn:li:seniority:1':'Entry'};
const typeMap = {'ENGAGEMENT':'Engagement','BRAND_AWARENESS':'Brand Awareness','WEBSITE_VISIT':'Website Visits','LEAD_GENERATION':'Lead Generation','JOB_APPLICANT':'Job Applicants'};

// LinkedIn Industry Taxonomy v2 — IDs >148 not available via /v2/industries API
const INDUSTRY_V2 = {"150":"Horticulture","201":"Farming, Ranching, Forestry","256":"Ranching and Fisheries","298":"Forestry and Logging","332":"Oil, Gas, and Mining","341":"Coal Mining","345":"Metal Ore Mining","356":"Nonmetallic Mineral Mining","382":"Electric Power Transmission, Control, and Distribution","383":"Electric Power Generation","384":"Hydroelectric Power Generation","385":"Fossil Fuel Electric Power Generation","386":"Nuclear Electric Power Generation","387":"Solar Electric Power Generation","388":"Environmental Quality Programs","389":"Geothermal Electric Power Generation","390":"Biomass Electric Power Generation","397":"Natural Gas Distribution","398":"Water, Waste, Steam, and Air Conditioning Services","400":"Water Supply and Irrigation Systems","404":"Steam and Air-Conditioning Supply","406":"Building Construction","408":"Residential Building Construction","413":"Nonresidential Building Construction","419":"Utility System Construction","428":"Subdivision of Land","431":"Highway, Street, and Bridge Construction","435":"Specialty Trade Contractors","436":"Building Structure and Exterior Contractors","453":"Building Equipment Contractors","460":"Building Finishing Contractors","481":"Animal Feed Manufacturing","495":"Sugar and Confectionery Product Manufacturing","504":"Fruit and Vegetable Preserves Manufacturing","521":"Meat Products Manufacturing","528":"Seafood Product Manufacturing","529":"Baked Goods Manufacturing","562":"Breweries","564":"Distilleries","598":"Apparel Manufacturing","615":"Fashion Accessories Manufacturing","616":"Leather Product Manufacturing","622":"Footwear Manufacturing","625":"Women's Handbag Manufacturing","679":"Oil and Coal Product Manufacturing","690":"Chemical Raw Materials Manufacturing","703":"Artificial Rubber and Synthetic Fiber Manufacturing","709":"Agricultural Chemical Manufacturing","722":"Paint, Coating, and Adhesive Manufacturing","727":"Soap and Cleaning Product Manufacturing","743":"Plastics and Rubber Product Manufacturing","763":"Rubber Products Manufacturing","773":"Clay and Refractory Products Manufacturing","779":"Glass Product Manufacturing","784":"Wood Product Manufacturing","794":"Lime and Gypsum Products Manufacturing","799":"Abrasives and Nonmetallic Minerals Manufacturing","807":"Primary Metal Manufacturing","840":"Fabricated Metal Products","849":"Cutlery and Handtool Manufacturing","852":"Architectural and Structural Metal Manufacturing","861":"Boilers, Tanks, and Shipping Container Manufacturing","871":"Construction Hardware Manufacturing","873":"Spring and Wire Product Manufacturing","876":"Turned Products and Fastener Manufacturing","883":"Metal Treatments","887":"Metal Valve, Ball, and Roller Manufacturing","901":"Agriculture, Construction, Mining Machinery Manufacturing","918":"Commercial and Service Industry Machinery Manufacturing","923":"HVAC and Refrigeration Equipment Manufacturing","928":"Metalworking Machinery Manufacturing","935":"Engines and Power Transmission Equipment Manufacturing","964":"Communications Equipment Manufacturing","973":"Audio and Video Equipment Manufacturing","983":"Measuring and Control Instrument Manufacturing","994":"Magnetic and Optical Media Manufacturing","998":"Electric Lighting Equipment Manufacturing","1005":"Household Appliance Manufacturing","1029":"Transportation Equipment Manufacturing","1042":"Motor Vehicle Parts Manufacturing","1080":"Household and Institutional Furniture Manufacturing","1090":"Office Furniture and Fixtures Manufacturing","1095":"Mattress and Blinds Manufacturing","1128":"Wholesale Motor Vehicles and Parts","1137":"Wholesale Furniture and Home Furnishings","1153":"Wholesale Photography Equipment and Supplies","1157":"Wholesale Computer Equipment","1166":"Wholesale Metals and Minerals","1171":"Wholesale Appliances, Electrical, and Electronics","1178":"Wholesale Hardware, Plumbing, Heating Equipment","1187":"Wholesale Machinery","1206":"Wholesale Recyclable Materials","1208":"Wholesale Luxury Goods and Jewelry","1212":"Wholesale Paper Products","1221":"Wholesale Drugs and Sundries","1222":"Wholesale Apparel and Sewing Supplies","1230":"Wholesale Footwear","1231":"Wholesale Food and Beverage","1250":"Wholesale Raw Farm Products","1257":"Wholesale Chemical and Allied Products","1262":"Wholesale Petroleum and Petroleum Products","1267":"Wholesale Alcoholic Beverages","1285":"Internet Marketplace Platforms","1292":"Retail Motor Vehicles","1309":"Retail Furniture and Home Furnishings","1319":"Retail Appliances, Electrical, and Electronic Equipment","1324":"Retail Building Materials and Garden Equipment","1339":"Food and Beverage Retail","1359":"Retail Health and Personal Care Products","1370":"Retail Gasoline","1407":"Retail Musical Instruments","1409":"Retail Books and Printed News","1423":"Retail Florists","1424":"Retail Office Supplies and Gifts","1431":"Retail Recyclable Materials & Used Merchandise","1445":"Online and Mail Order Retail","1481":"Rail Transportation","1495":"Ground Passenger Transportation","1497":"Urban Transit Services","1504":"Interurban and Rural Bus Services","1505":"Taxi and Limousine Services","1512":"School and Employee Bus Services","1517":"Shuttles and Special Needs Transportation Services","1520":"Pipeline Transportation","1532":"Sightseeing Transportation","1573":"Postal Services","1594":"Technology, Information and Media","1600":"Periodical Publishing","1602":"Book Publishing","1611":"Movies and Sound Recording","1623":"Sound Recording","1625":"Sheet Music Publishing","1633":"Radio and Television Broadcasting","1641":"Cable and Satellite Programming","1644":"Telecommunications Carriers","1649":"Satellite Telecommunications","1673":"Credit Intermediation","1678":"Savings Institutions","1696":"Loan Brokers","1713":"Securities and Commodity Exchanges","1720":"Investment Advice","1725":"Insurance Carriers","1737":"Insurance Agencies and Brokerages","1738":"Claims Adjusting, Actuarial Services","1742":"Funds and Trusts","1743":"Insurance and Employee Benefit Funds","1745":"Pension Funds","1750":"Trusts and Estates","1757":"Real Estate and Equipment Rental Services","1759":"Leasing Residential Real Estate","1770":"Real Estate Agents and Brokers","1779":"Equipment Rental Services","1786":"Consumer Goods Rental","1798":"Commercial and Industrial Equipment Rental","1810":"Professional Services","1855":"IT System Design Services","1862":"Marketing Services","1905":"Holding Companies","1909":"Industry Associations","1911":"Professional Organizations","1912":"Administrative and Support Services","1916":"Office Administration","1923":"Executive Search Services","1925":"Temporary Help Services","1931":"Telephone Call Centers","1938":"Collection Agencies","1956":"Security Guards and Patrol Services","1958":"Security Systems Services","1965":"Janitorial Services","1981":"Waste Collection","1986":"Waste Treatment and Disposal","1999":"Education","2012":"Secretarial Schools","2018":"Technical and Vocational Training","2019":"Cosmetology and Barber Schools","2020":"Flight Training","2025":"Fine Arts Schools","2027":"Sports and Recreation Instruction","2029":"Language Schools","2040":"Physicians","2045":"Dentists","2048":"Chiropractors","2050":"Optometrists","2054":"Physical, Occupational and Speech Therapists","2060":"Family Planning Centers","2063":"Outpatient Care Centers","2069":"Medical and Diagnostic Laboratories","2074":"Home Health Care Services","2077":"Ambulance Services","2081":"Hospitals","2091":"Nursing Homes and Residential Care Facilities","2112":"Services for the Elderly and Disabled","2115":"Community Services","2122":"Emergency and Relief Services","2125":"Vocational Rehabilitation Services","2128":"Child Day Care Services","2130":"Performing Arts and Spectator Sports","2133":"Theater Companies","2135":"Dance Companies","2139":"Circuses and Magic Shows","2142":"Sports Teams and Clubs","2143":"Racetracks","2159":"Museums","2161":"Historical Sites","2163":"Zoos and Botanical Gardens","2167":"Amusement Parks and Arcades","2179":"Golf Courses and Country Clubs","2181":"Skiing Facilities","2190":"Accommodation Services","2194":"Hotels and Motels","2197":"Bed-and-Breakfasts, Hostels, Homestays","2212":"Caterers","2214":"Mobile Food Services","2217":"Bars, Taverns, and Nightclubs","2225":"Repair and Maintenance","2226":"Vehicle Repair and Maintenance","2240":"Electronic and Precision Equipment Maintenance","2247":"Commercial and Industrial Machinery Maintenance","2253":"Reupholstery and Furniture Repair","2255":"Footwear and Leather Goods Repair","2258":"Personal and Laundry Services","2259":"Personal Care Services","2272":"Laundry and Drycleaning Services","2282":"Pet Services","2318":"Household Services","2353":"Health and Human Services","2358":"Public Health","2360":"Public Assistance Programs","2366":"Air, Water, and Waste Program Management","2368":"Conservation Programs","2369":"Housing and Community Development","2374":"Community Development and Urban Planning","2375":"Economic Programs","2391":"Military and International Affairs","2401":"Operations Consulting","2458":"Data Infrastructure and Analytics","2468":"Electrical Equipment Manufacturing","2489":"Wind Electric Power Generation","2500":"Wineries","2934":"Landscaping Services","3065":"Courts of Law","3068":"Correctional Institutions","3070":"Fire Protection","3081":"Housing Programs","3085":"Transportation Programs","3086":"Utilities Administration","3089":"Space Research and Technology","3095":"Oil Extraction","3096":"Natural Gas Extraction","3099":"Embedded Software Products","3100":"Mobile Computing Software Products","3101":"Desktop Computing Software Products","3102":"IT System Custom Software Development","3103":"IT System Operations and Maintenance","3104":"IT System Installation and Disposal","3105":"IT System Training and Support","3106":"IT System Data Services","3107":"IT System Testing and Evaluation","3124":"Internet News","3125":"Blogs","3126":"Interior Design","3127":"Social Networking Platforms","3128":"Business Intelligence Platforms","3129":"Business Content","3130":"Data Security Software Products","3131":"Mobile Gaming Apps","3132":"Internet Publishing","3133":"Media & Telecommunications","3134":"Blockchain Services","3186":"Retail Art Dealers","3240":"Renewable Energy Power Generation","3241":"Renewable Energy Equipment Manufacturing","3242":"Engineering Services","3243":"Services for Renewable Energy","3244":"Digital Accessibility Services","3245":"Accessible Hardware Manufacturing","3246":"Accessible Architecture and Design","3247":"Robot Manufacturing","3248":"Robotics Engineering","3249":"Surveying and Mapping Services","3250":"Retail Pharmacies","3251":"Climate Technology Product Manufacturing","3252":"Climate Data and Analytics","3253":"Alternative Fuel Vehicle Manufacturing","3254":"Smart Meter Manufacturing","3255":"Fuel Cell Manufacturing","3256":"Regenerative Design"};

function formatCompanySize(val) {
  // SIZE_1001_TO_5000 -> "1,001 - 5,000", SIZE_10001_OR_MORE -> "10,001+"
  const m = val.match(/SIZE_(\d+)_TO_(\d+)/);
  if (m) return `${Number(m[1]).toLocaleString()} - ${Number(m[2]).toLocaleString()}`;
  const m2 = val.match(/SIZE_(\d+)_OR_MORE/);
  if (m2) return `${Number(m2[1]).toLocaleString()}+`;
  const m3 = val.match(/SIZE_(\d+)/);
  if (m3) return Number(m3[1]).toLocaleString();
  return val;
}

async function api(url, headers, retries=2) {
  for (let i=0; i<=retries; i++) {
    try {
      return await this.helpers.httpRequest({ method:'GET', url, headers });
    } catch(e) {
      if (i < retries) { await new Promise(r=>setTimeout(r,500*(i+1))); continue; }
      return null;
    }
  }
}
const apiFn = api.bind(this);

async function batch(tasks, size=5) {
  const results = [];
  for (let i = 0; i < tasks.length; i += size) {
    const chunk = tasks.slice(i, i + size);
    const res = await Promise.all(chunk.map(fn => fn()));
    results.push(...res);
    if (i + size < tasks.length) await new Promise(r => setTimeout(r, 200));
  }
  return results;
}

console.log(`Fetching ${campaignIds.length} campaigns in parallel...`);

// STEP 1: Fetch all campaign details in parallel (batches of 5)
const campDataList = await batch(
  campaignIds.map(id => () => apiFn(`https://api.linkedin.com/rest/adAccounts/${accountId}/adCampaigns/${id}`, restHeaders)),
  5
);

const validCampaigns = [];
for (let i = 0; i < campaignIds.length; i++) {
  const campData = campDataList[i];
  if (!campData) continue;
  const campId = campaignIds[i];
  const startMs = campData.runSchedule?.start || 0;
  const startDt = startMs ? new Date(startMs) : new Date(2025,0,1);
  const geoUrns = [];
  for (const clause of (campData.targetingCriteria?.include?.and || [])) {
    if (clause.or) {
      for (const [key, vals] of Object.entries(clause.or)) {
        if (key.toLowerCase().includes('geo') || key.toLowerCase().includes('location') || key.toLowerCase().includes('country'))
          geoUrns.push(...vals);
      }
    }
  }
  let displayName = campData.name || `Campaign ${campId}`;
  const nm = displayName.match(/^([^-]+)/)?.[1]?.trim();
  if (nm && nm.length < displayName.length && nm.length > 2) displayName = nm;
  const now = new Date();
  const dr = `(start:(year:${startDt.getFullYear()},month:${startDt.getMonth()+1},day:${startDt.getDate()}),end:(year:${now.getFullYear()},month:${now.getMonth()+1},day:${now.getDate()}))`;
  validCampaigns.push({ campId, campData, startMs, startDt, geoUrns, displayName, dr });
}

console.log(`${validCampaigns.length} valid campaigns. Fetching analytics + demographics...`);

// STEP 2: Fetch analytics + demographics per campaign
const FIELDS_BATCH1 = 'impressions,clicks,totalEngagements,likes,comments,shares,follows,reactions,costInUsd,landingPageClicks,otherEngagements,companyPageClicks,externalWebsiteConversions,oneClickLeads,approximateUniqueImpressions';
const FIELDS_BATCH2 = 'videoViews,videoFirstQuartileCompletions,videoMidpointCompletions,videoThirdQuartileCompletions,videoCompletions,fullScreenPlays';
const MONTHLY_FIELDS = 'impressions,clicks,costInUsd,totalEngagements';
const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const allResults = await batch(
  validCampaigns.map(vc => async () => {
    const { campId, dr } = vc;
    const urn = `urn%3Ali%3AsponsoredCampaign%3A${campId}`;
    const base = `https://api.linkedin.com/v2/adAnalyticsV2?q=analytics`;
    const [analyticsBatch1, analyticsBatch2, crAnalytics, monthlyData, ...demoResults] = await Promise.all([
      apiFn(`${base}&pivot=CAMPAIGN&dateRange=${dr}&timeGranularity=ALL&campaigns=List(${urn})&fields=${FIELDS_BATCH1}`, v2Headers),
      apiFn(`${base}&pivot=CAMPAIGN&dateRange=${dr}&timeGranularity=ALL&campaigns=List(${urn})&fields=${FIELDS_BATCH2}`, v2Headers),
      apiFn(`${base}&pivot=CREATIVE&dateRange=${dr}&timeGranularity=ALL&campaigns=List(${urn})&fields=impressions,clicks,totalEngagements,pivotValues&count=25`, v2Headers),
      apiFn(`${base}&pivot=CAMPAIGN&dateRange=${dr}&timeGranularity=MONTHLY&campaigns=List(${urn})&fields=${MONTHLY_FIELDS}`, v2Headers),
      ...PIVOTS.map(p => apiFn(`${base}&pivot=${p}&dateRange=${dr}&timeGranularity=ALL&campaigns=List(${urn})&fields=impressions,clicks,pivotValues&count=25`, v2Headers))
    ]);
    // Merge the two analytics batches
    const stats1 = analyticsBatch1?.elements?.[0] || {};
    const stats2 = analyticsBatch2?.elements?.[0] || {};
    const analytics = { elements: [{ ...stats1, ...stats2 }] };
    // Parse monthly trends
    const monthlyTrends = (monthlyData?.elements || []).map(el => {
      const s = el.dateRange?.start;
      const monthLabel = s ? `${MONTH_NAMES[s.month - 1]} ${s.year}` : 'Unknown';
      return {
        month: monthLabel,
        impressions: el.impressions || 0,
        clicks: el.clicks || 0,
        cost: parseFloat(el.costInUsd || '0') || 0,
        engagements: el.totalEngagements || 0
      };
    }).sort((a, b) => {
      const parseMonth = m => { const parts = m.split(' '); return (parseInt(parts[1])||0)*100 + MONTH_NAMES.indexOf(parts[0]); };
      return parseMonth(a.month) - parseMonth(b.month);
    });
    return { analytics, crAnalytics, demoResults, monthlyTrends };
  }),
  3
);

console.log('Analytics done. Fetching creative details + resolving demographics...');

// STEP 3: Build campaign objects with raw demographics
const campaigns = [];
for (let idx = 0; idx < validCampaigns.length; idx++) {
  const vc = validCampaigns[idx];
  const { campId, campData, startMs, geoUrns, displayName } = vc;
  const { analytics, crAnalytics, demoResults, monthlyTrends } = allResults[idx];
  const stats = analytics?.elements?.[0] || {};
  const crStats = (crAnalytics?.elements || []).sort((a,b) => (b.impressions||0)-(a.impressions||0));

  const crEntries = crStats.slice(0, 10).filter(cs => (cs.pivotValues||[])[0]);
  const creativeResults = await batch(
    crEntries.map(cs => async () => {
      const crUrn = cs.pivotValues[0];
      const encoded = encodeURIComponent(crUrn);
      const crData = await apiFn(`https://api.linkedin.com/rest/adAccounts/${accountId}/creatives/${encoded}`, restHeaders);
      let imageUrl = null;
      if (crData?.content?.reference) {
        const shareId = crData.content.reference.split(':').pop();
        const shareData = await apiFn(`https://api.linkedin.com/v2/shares/${shareId}`, v2Headers);
        imageUrl = shareData?.content?.contentEntities?.[0]?.thumbnails?.[0]?.resolvedUrl || null;
      }
      return {
        id: crUrn.split(':').pop(),
        name: crData?.name || `Creative ${crUrn.split(':').pop()}`,
        impressions: cs.impressions||0, clicks: cs.clicks||0,
        image_url: imageUrl
      };
    }),
    5
  );

  const campDemo = {};
  for (let p = 0; p < PIVOTS.length; p++) {
    const demoData = demoResults[p];
    if (demoData?.elements) {
      campDemo[PIVOTS[p]] = demoData.elements.map(el => ({
        pivotValue: (el.pivotValues||[])[0]||'Unknown',
        impressions: el.impressions||0, clicks: el.clicks||0
      })).sort((a,b) => b.impressions - a.impressions);
    }
  }

  const imp = stats.impressions || null;
  const clk = stats.clicks || null;
  const eng = stats.totalEngagements || null;
  const costUsd = parseFloat(stats.costInUsd || '0') || null;

  campaigns.push({
    id: campId, name: campData.name, display_name: displayName,
    campaign_type: typeMap[campData.objectiveType]||campData.objectiveType?.replace(/_/g,' ')||'N/A',
    status: campData.status,
    start_date: startMs ? new Date(startMs).toISOString().split('T')[0] : null,
    geo_urns: geoUrns, geo_display: resolveGeo(geoUrns),
    impressions: imp, clicks: clk,
    engagements: eng,
    likes: stats.likes || null,
    reactions: stats.reactions || null,
    comments: stats.comments || null,
    shares: stats.shares || null,
    follows: stats.follows || null,
    cost_usd: costUsd,
    landing_page_clicks: stats.landingPageClicks || null,
    company_page_clicks: stats.companyPageClicks || null,
    other_engagements: stats.otherEngagements || null,
    conversions: stats.externalWebsiteConversions || null,
    one_click_leads: stats.oneClickLeads || null,
    video_views: stats.videoViews || null,
    video_completions: stats.videoCompletions || null,
    video_first_quartile: stats.videoFirstQuartileCompletions || null,
    video_midpoint: stats.videoMidpointCompletions || null,
    video_third_quartile: stats.videoThirdQuartileCompletions || null,
    full_screen_plays: stats.fullScreenPlays || null,
    ctr: (clk && imp) ? (clk / imp * 100) : null,
    cpc: (costUsd && clk) ? (costUsd / clk) : null,
    cpm: (costUsd && imp) ? (costUsd / imp * 1000) : null,
    cost_per_engagement: (costUsd && eng) ? (costUsd / eng) : null,
    engagement_rate: (eng && imp) ? (eng / imp * 100) : null,
    monthly_trends: monthlyTrends,
    creatives: creativeResults, demographics: campDemo
  });
  console.log(`  ${displayName}: ${imp||0} imp, ${creativeResults.length} creatives`);
}

// STEP 4: Collect all unique IDs across all campaigns for batch resolution
const allTitleIds = new Set();
const allFunctionIds = new Set();
const allIndustryIds = new Set();
const allGeoIds = new Set();
const allOrgIds = new Set();

for (const camp of campaigns) {
  const demo = camp.demographics;
  (demo.MEMBER_JOB_TITLE||[]).forEach(d => allTitleIds.add(d.pivotValue.split(':').pop()));
  (demo.MEMBER_JOB_FUNCTION||[]).forEach(d => allFunctionIds.add(d.pivotValue.split(':').pop()));
  (demo.MEMBER_INDUSTRY||[]).forEach(d => allIndustryIds.add(d.pivotValue.split(':').pop()));
  (demo.MEMBER_REGION_V2||[]).forEach(d => allGeoIds.add(d.pivotValue.split(':').pop()));
  (demo.MEMBER_COUNTRY_V2||[]).forEach(d => allGeoIds.add(d.pivotValue.split(':').pop()));
  (demo.MEMBER_COMPANY||[]).forEach(d => { if (d.pivotValue.includes('organization')) allOrgIds.add(d.pivotValue.split(':').pop()); });
}

console.log(`Resolving: ${allTitleIds.size} titles, ${allFunctionIds.size} functions, ${allIndustryIds.size} industries, ${allGeoIds.size} geos, ${allOrgIds.size} orgs`);

// Batch resolve titles, industries, and geos (these support batch API)
const titleMap = {};
const industryMap = {};
const geoMap = {};

const batchResolves = [];

if (allTitleIds.size > 0) {
  // Batch in groups of 20 to avoid URL length limits
  const titleIdArr = [...allTitleIds];
  for (let i = 0; i < titleIdArr.length; i += 20) {
    const chunk = titleIdArr.slice(i, i + 20);
    batchResolves.push(apiFn(`https://api.linkedin.com/v2/titles?ids=List(${chunk.join(',')})`, v2Headers).then(d => {
      for (const [id, val] of Object.entries(d?.results||{})) {
        titleMap[`urn:li:title:${id}`] = val?.name?.localized?.en_US || id;
      }
    }));
  }
}

if (allIndustryIds.size > 0) {
  const indIdArr = [...allIndustryIds];
  // First populate from static v2 map
  for (const id of indIdArr) {
    if (INDUSTRY_V2[id]) industryMap[`urn:li:industry:${id}`] = INDUSTRY_V2[id];
  }
  // Then try API for any remaining (standard IDs 1-148)
  const unresolvedInds = indIdArr.filter(id => !industryMap[`urn:li:industry:${id}`]);
  for (let i = 0; i < unresolvedInds.length; i += 20) {
    const chunk = unresolvedInds.slice(i, i + 20);
    batchResolves.push(apiFn(`https://api.linkedin.com/v2/industries?ids=List(${chunk.join(',')})`, v2Headers).then(d => {
      for (const [id, val] of Object.entries(d?.results||{})) {
        industryMap[`urn:li:industry:${id}`] = val?.name?.localized?.en_US || id;
      }
    }));
  }
}

if (allGeoIds.size > 0) {
  const geoIdArr = [...allGeoIds];
  for (let i = 0; i < geoIdArr.length; i += 20) {
    const chunk = geoIdArr.slice(i, i + 20);
    batchResolves.push(apiFn(`https://api.linkedin.com/v2/geo?ids=List(${chunk.join(',')})`, v2Headers).then(d => {
      for (const [id, val] of Object.entries(d?.results||{})) {
        geoMap[`urn:li:geo:${id}`] = val?.defaultLocalizedName?.value || id;
      }
    }));
  }
}

await Promise.all(batchResolves);

// Resolve functions individually (no batch API)
const functionMap = {};
const funcIds = [...allFunctionIds];
if (funcIds.length > 0) {
  const funcResults = await batch(
    funcIds.map(id => () => apiFn(`https://api.linkedin.com/v2/functions/${id}`, v2Headers)),
    5
  );
  for (let i = 0; i < funcIds.length; i++) {
    functionMap[`urn:li:function:${funcIds[i]}`] = funcResults[i]?.name?.localized?.en_US || funcIds[i];
  }
}

// Resolve organizations via batch organizationsLookup (REST API)
const orgMap = {};
const orgIds = [...allOrgIds];
if (orgIds.length > 0) {
  for (let i = 0; i < orgIds.length; i += 20) {
    const chunk = orgIds.slice(i, i + 20);
    const idList = chunk.join(',');
    const orgData = await apiFn(`https://api.linkedin.com/rest/organizationsLookup?ids=List(${idList})`, restHeaders);
    if (orgData?.results) {
      for (const [id, val] of Object.entries(orgData.results)) {
        orgMap[`urn:li:organization:${id}`] = val?.localizedName || `Company #${id}`;
      }
    }
    // Mark any missing orgs
    for (const id of chunk) {
      if (!orgMap[`urn:li:organization:${id}`]) orgMap[`urn:li:organization:${id}`] = `Company #${id}`;
    }
    if (i + 20 < orgIds.length) await new Promise(r => setTimeout(r, 200));
  }
}

// Resolve seniorities dynamically (individual calls since batch doesn't work)
const seniorityMap = {...SENIORITY_MAP};
const unresolvedSeniorities = new Set();
for (const camp of campaigns) {
  (camp.demographics.MEMBER_SENIORITY||[]).forEach(d => {
    if (!seniorityMap[d.pivotValue]) unresolvedSeniorities.add(d.pivotValue.split(':').pop());
  });
}
if (unresolvedSeniorities.size > 0) {
  const senIds = [...unresolvedSeniorities];
  const senResults = await batch(
    senIds.map(id => () => apiFn(`https://api.linkedin.com/v2/seniorities/${id}`, v2Headers)),
    5
  );
  for (let i = 0; i < senIds.length; i++) {
    const name = senResults[i]?.name?.localized?.en_US;
    if (name) seniorityMap[`urn:li:seniority:${senIds[i]}`] = name;
  }
}

// STEP 5: Apply resolved names to all campaigns
for (const camp of campaigns) {
  const demo = camp.demographics;
  if (demo.MEMBER_JOB_TITLE) demo.MEMBER_JOB_TITLE = demo.MEMBER_JOB_TITLE.map(d => ({...d, displayName: titleMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_JOB_FUNCTION) demo.MEMBER_JOB_FUNCTION = demo.MEMBER_JOB_FUNCTION.map(d => ({...d, displayName: functionMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_INDUSTRY) demo.MEMBER_INDUSTRY = demo.MEMBER_INDUSTRY.map(d => {
    const id = d.pivotValue.split(':').pop();
    return {...d, displayName: industryMap[d.pivotValue] || `Industry #${id}`};
  });
  if (demo.MEMBER_REGION_V2) demo.MEMBER_REGION_V2 = demo.MEMBER_REGION_V2.map(d => ({...d, displayName: geoMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_COUNTRY_V2) demo.MEMBER_COUNTRY_V2 = demo.MEMBER_COUNTRY_V2.map(d => ({...d, displayName: geoMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_COMPANY) demo.MEMBER_COMPANY = demo.MEMBER_COMPANY.map(d => ({...d, displayName: orgMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_SENIORITY) demo.MEMBER_SENIORITY = demo.MEMBER_SENIORITY.map(d => ({...d, displayName: seniorityMap[d.pivotValue] || d.pivotValue.split(':').pop()}));
  if (demo.MEMBER_COMPANY_SIZE) demo.MEMBER_COMPANY_SIZE = demo.MEMBER_COMPANY_SIZE.map(d => ({...d, displayName: formatCompanySize(d.pivotValue)}));
}

console.log(`Done! ${campaigns.length} campaigns processed with resolved demographics.`);
const report_date = new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'2-digit',year:'numeric'}).replace(/\//g,'-');
return [{json:{campaigns,report_date}}];'''
        break

with open(WORKFLOW_PATH, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2)

print("workflow.json updated successfully")
