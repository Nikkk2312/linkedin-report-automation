"""
LinkedIn API client for fetching campaign data, analytics, demographics, and creatives.
Mirrors the n8n workflow logic but implemented in Python using requests.
"""

import logging
import time
import re
import requests

logger = logging.getLogger(__name__)


# ─── CUSTOM EXCEPTIONS ───────────────────────────────────────────────────────

class LinkedInAPIError(Exception):
    """Base exception for LinkedIn API errors."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class LinkedInAuthError(LinkedInAPIError):
    """Raised on 401 Unauthorized responses from LinkedIn API."""

    def __init__(self, message="LinkedIn API authentication failed. Check your access token.", response=None):
        super().__init__(message, status_code=401, response=response)


class LinkedInRateLimitError(LinkedInAPIError):
    """Raised on 429 Too Many Requests responses from LinkedIn API."""

    def __init__(self, message="LinkedIn API rate limit exceeded.", retry_after=None, response=None):
        super().__init__(message, status_code=429, response=response)
        self.retry_after = retry_after


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

LINKEDIN_API_BASE = "https://api.linkedin.com"

FIELDS_BATCH1 = (
    "impressions,clicks,totalEngagements,likes,comments,shares,follows,"
    "reactions,costInUsd,costInLocalCurrency,landingPageClicks,otherEngagements,"
    "companyPageClicks,externalWebsiteConversions,oneClickLeads,"
    "approximateUniqueImpressions,commentLikes,opens,sends,textUrlClicks"
)

FIELDS_BATCH2 = (
    "videoViews,videoStarts,videoCompletions,videoFirstQuartileCompletions,"
    "videoMidpointCompletions,videoThirdQuartileCompletions,fullScreenPlays,"
    "videoWatchTime,averageDwellTime,documentCompletions,"
    "documentFirstQuartileCompletions,documentMidpointCompletions,"
    "documentThirdQuartileCompletions,downloadClicks,headlineClicks,"
    "headlineImpressions,actionClicks,adUnitClicks,oneClickLeadFormOpens,subscriptionClicks"
)

FIELDS_BATCH3 = (
    "viralImpressions,viralClicks,viralLikes,viralComments,viralShares,"
    "viralFollows,viralReactions,viralTotalEngagements,viralLandingPageClicks,"
    "viralCompanyPageClicks,viralOtherEngagements,viralExternalWebsiteConversions,"
    "viralOneClickLeads,viralOneClickLeadFormOpens,viralFullScreenPlays,"
    "viralVideoViews,viralVideoStarts,viralVideoCompletions,"
    "viralVideoFirstQuartileCompletions,viralVideoMidpointCompletions"
)

FIELDS_BATCH4 = (
    "viralVideoThirdQuartileCompletions,externalWebsitePostClickConversions,"
    "externalWebsitePostViewConversions,qualifiedLeads,"
    "validWorkEmailLeads,talentLeads,leadGenerationMailContactInfoShares,"
    "leadGenerationMailInterestedClicks,jobApplications,jobApplyClicks,"
    "postClickJobApplications,postViewJobApplications,"
    "postClickRegistrations,postViewRegistrations,registrations,"
    "costPerQualifiedLead,appointmentsScheduled"
)

FIELDS_BATCH5 = (
    "eventViews,eventWatchTime,averageEventWatchTime,"
    "eventViewsOver15Seconds,eventViewsOver30Seconds,eventViewsOver2Minutes,"
    "costPerEventView"
)
MONTHLY_FIELDS = "impressions,clicks,costInUsd,totalEngagements"

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

PIVOTS = [
    'MEMBER_COMPANY', 'MEMBER_SENIORITY', 'MEMBER_INDUSTRY',
    'MEMBER_COMPANY_SIZE', 'MEMBER_JOB_FUNCTION', 'MEMBER_JOB_TITLE',
    'MEMBER_REGION_V2', 'MEMBER_COUNTRY_V2',
]

# Additional pivots (non-demographic, different handling)
EXTRA_PIVOTS = [
    'IMPRESSION_DEVICE_TYPE',
    'SERVING_LOCATION',
]

SENIORITY_MAP = {
    'urn:li:seniority:10': 'Owner',
    'urn:li:seniority:9': 'Partner',
    'urn:li:seniority:8': 'Owner',
    'urn:li:seniority:7': 'Partner',
    'urn:li:seniority:6': 'CXO',
    'urn:li:seniority:5': 'VP',
    'urn:li:seniority:4': 'Director',
    'urn:li:seniority:3': 'Manager',
    'urn:li:seniority:2': 'Senior',
    'urn:li:seniority:1': 'Entry',
}

CAMPAIGN_TYPE_MAP = {
    'ENGAGEMENT': 'Engagement',
    'BRAND_AWARENESS': 'Brand Awareness',
    'WEBSITE_VISIT': 'Website Visits',
    'LEAD_GENERATION': 'Lead Generation',
    'JOB_APPLICANT': 'Job Applicants',
    'VIDEO_VIEWS': 'Video Views',
    'WEBSITE_CONVERSIONS': 'Website Conversions',
}

GEO_MAP = {
    'urn:li:geo:103644278': 'US',
    'urn:li:geo:101174742': 'Canada',
    'urn:li:geo:102713980': 'India',
    'urn:li:geo:104305776': 'UAE',
    'urn:li:geo:102890719': 'UK',
    'urn:li:geo:101282230': 'Germany',
    'urn:li:geo:100961908': 'Australia',
    'urn:li:geo:102956297': 'Mumbai',
    'urn:li:geo:106164952': 'Mumbai',
    'urn:li:geo:108393811': 'Navi Mumbai',
    'urn:li:geo:101389470': 'Indore',
}

# LinkedIn Industry Taxonomy v2 - IDs >148 not available via /v2/industries API
INDUSTRY_V2 = {
    "150": "Horticulture", "201": "Farming, Ranching, Forestry",
    "256": "Ranching and Fisheries", "298": "Forestry and Logging",
    "332": "Oil, Gas, and Mining", "341": "Coal Mining",
    "345": "Metal Ore Mining", "356": "Nonmetallic Mineral Mining",
    "382": "Electric Power Transmission, Control, and Distribution",
    "383": "Electric Power Generation",
    "384": "Hydroelectric Power Generation",
    "385": "Fossil Fuel Electric Power Generation",
    "386": "Nuclear Electric Power Generation",
    "387": "Solar Electric Power Generation",
    "388": "Environmental Quality Programs",
    "389": "Geothermal Electric Power Generation",
    "390": "Biomass Electric Power Generation",
    "397": "Natural Gas Distribution",
    "398": "Water, Waste, Steam, and Air Conditioning Services",
    "400": "Water Supply and Irrigation Systems",
    "404": "Steam and Air-Conditioning Supply",
    "406": "Building Construction",
    "408": "Residential Building Construction",
    "413": "Nonresidential Building Construction",
    "419": "Utility System Construction",
    "428": "Subdivision of Land",
    "431": "Highway, Street, and Bridge Construction",
    "435": "Specialty Trade Contractors",
    "436": "Building Structure and Exterior Contractors",
    "453": "Building Equipment Contractors",
    "460": "Building Finishing Contractors",
    "481": "Animal Feed Manufacturing",
    "495": "Sugar and Confectionery Product Manufacturing",
    "504": "Fruit and Vegetable Preserves Manufacturing",
    "521": "Meat Products Manufacturing",
    "528": "Seafood Product Manufacturing",
    "529": "Baked Goods Manufacturing",
    "562": "Breweries", "564": "Distilleries",
    "598": "Apparel Manufacturing",
    "615": "Fashion Accessories Manufacturing",
    "616": "Leather Product Manufacturing",
    "622": "Footwear Manufacturing",
    "625": "Women's Handbag Manufacturing",
    "679": "Oil and Coal Product Manufacturing",
    "690": "Chemical Raw Materials Manufacturing",
    "703": "Artificial Rubber and Synthetic Fiber Manufacturing",
    "709": "Agricultural Chemical Manufacturing",
    "722": "Paint, Coating, and Adhesive Manufacturing",
    "727": "Soap and Cleaning Product Manufacturing",
    "743": "Plastics and Rubber Product Manufacturing",
    "763": "Rubber Products Manufacturing",
    "773": "Clay and Refractory Products Manufacturing",
    "779": "Glass Product Manufacturing",
    "784": "Wood Product Manufacturing",
    "794": "Lime and Gypsum Products Manufacturing",
    "799": "Abrasives and Nonmetallic Minerals Manufacturing",
    "807": "Primary Metal Manufacturing",
    "840": "Fabricated Metal Products",
    "849": "Cutlery and Handtool Manufacturing",
    "852": "Architectural and Structural Metal Manufacturing",
    "861": "Boilers, Tanks, and Shipping Container Manufacturing",
    "871": "Construction Hardware Manufacturing",
    "873": "Spring and Wire Product Manufacturing",
    "876": "Turned Products and Fastener Manufacturing",
    "883": "Metal Treatments",
    "887": "Metal Valve, Ball, and Roller Manufacturing",
    "901": "Agriculture, Construction, Mining Machinery Manufacturing",
    "918": "Commercial and Service Industry Machinery Manufacturing",
    "923": "HVAC and Refrigeration Equipment Manufacturing",
    "928": "Metalworking Machinery Manufacturing",
    "935": "Engines and Power Transmission Equipment Manufacturing",
    "964": "Communications Equipment Manufacturing",
    "973": "Audio and Video Equipment Manufacturing",
    "983": "Measuring and Control Instrument Manufacturing",
    "994": "Magnetic and Optical Media Manufacturing",
    "998": "Electric Lighting Equipment Manufacturing",
    "1005": "Household Appliance Manufacturing",
    "1029": "Transportation Equipment Manufacturing",
    "1042": "Motor Vehicle Parts Manufacturing",
    "1080": "Household and Institutional Furniture Manufacturing",
    "1090": "Office Furniture and Fixtures Manufacturing",
    "1095": "Mattress and Blinds Manufacturing",
    "1128": "Wholesale Motor Vehicles and Parts",
    "1137": "Wholesale Furniture and Home Furnishings",
    "1153": "Wholesale Photography Equipment and Supplies",
    "1157": "Wholesale Computer Equipment",
    "1166": "Wholesale Metals and Minerals",
    "1171": "Wholesale Appliances, Electrical, and Electronics",
    "1178": "Wholesale Hardware, Plumbing, Heating Equipment",
    "1187": "Wholesale Machinery",
    "1206": "Wholesale Recyclable Materials",
    "1208": "Wholesale Luxury Goods and Jewelry",
    "1212": "Wholesale Paper Products",
    "1221": "Wholesale Drugs and Sundries",
    "1222": "Wholesale Apparel and Sewing Supplies",
    "1230": "Wholesale Footwear",
    "1231": "Wholesale Food and Beverage",
    "1250": "Wholesale Raw Farm Products",
    "1257": "Wholesale Chemical and Allied Products",
    "1262": "Wholesale Petroleum and Petroleum Products",
    "1267": "Wholesale Alcoholic Beverages",
    "1285": "Internet Marketplace Platforms",
    "1292": "Retail Motor Vehicles",
    "1309": "Retail Furniture and Home Furnishings",
    "1319": "Retail Appliances, Electrical, and Electronic Equipment",
    "1324": "Retail Building Materials and Garden Equipment",
    "1339": "Food and Beverage Retail",
    "1359": "Retail Health and Personal Care Products",
    "1370": "Retail Gasoline",
    "1407": "Retail Musical Instruments",
    "1409": "Retail Books and Printed News",
    "1423": "Retail Florists",
    "1424": "Retail Office Supplies and Gifts",
    "1431": "Retail Recyclable Materials & Used Merchandise",
    "1445": "Online and Mail Order Retail",
    "1481": "Rail Transportation",
    "1495": "Ground Passenger Transportation",
    "1497": "Urban Transit Services",
    "1504": "Interurban and Rural Bus Services",
    "1505": "Taxi and Limousine Services",
    "1512": "School and Employee Bus Services",
    "1517": "Shuttles and Special Needs Transportation Services",
    "1520": "Pipeline Transportation",
    "1532": "Sightseeing Transportation",
    "1573": "Postal Services",
    "1594": "Technology, Information and Media",
    "1600": "Periodical Publishing",
    "1602": "Book Publishing",
    "1611": "Movies and Sound Recording",
    "1623": "Sound Recording",
    "1625": "Sheet Music Publishing",
    "1633": "Radio and Television Broadcasting",
    "1641": "Cable and Satellite Programming",
    "1644": "Telecommunications Carriers",
    "1649": "Satellite Telecommunications",
    "1673": "Credit Intermediation",
    "1678": "Savings Institutions",
    "1696": "Loan Brokers",
    "1713": "Securities and Commodity Exchanges",
    "1720": "Investment Advice",
    "1725": "Insurance Carriers",
    "1737": "Insurance Agencies and Brokerages",
    "1738": "Claims Adjusting, Actuarial Services",
    "1742": "Funds and Trusts",
    "1743": "Insurance and Employee Benefit Funds",
    "1745": "Pension Funds",
    "1750": "Trusts and Estates",
    "1757": "Real Estate and Equipment Rental Services",
    "1759": "Leasing Residential Real Estate",
    "1770": "Real Estate Agents and Brokers",
    "1779": "Equipment Rental Services",
    "1786": "Consumer Goods Rental",
    "1798": "Commercial and Industrial Equipment Rental",
    "1810": "Professional Services",
    "1855": "IT System Design Services",
    "1862": "Marketing Services",
    "1905": "Holding Companies",
    "1909": "Industry Associations",
    "1911": "Professional Organizations",
    "1912": "Administrative and Support Services",
    "1916": "Office Administration",
    "1923": "Executive Search Services",
    "1925": "Temporary Help Services",
    "1931": "Telephone Call Centers",
    "1938": "Collection Agencies",
    "1956": "Security Guards and Patrol Services",
    "1958": "Security Systems Services",
    "1965": "Janitorial Services",
    "1981": "Waste Collection",
    "1986": "Waste Treatment and Disposal",
    "1999": "Education",
    "2012": "Secretarial Schools",
    "2018": "Technical and Vocational Training",
    "2019": "Cosmetology and Barber Schools",
    "2020": "Flight Training",
    "2025": "Fine Arts Schools",
    "2027": "Sports and Recreation Instruction",
    "2029": "Language Schools",
    "2040": "Physicians",
    "2045": "Dentists",
    "2048": "Chiropractors",
    "2050": "Optometrists",
    "2054": "Physical, Occupational and Speech Therapists",
    "2060": "Family Planning Centers",
    "2063": "Outpatient Care Centers",
    "2069": "Medical and Diagnostic Laboratories",
    "2074": "Home Health Care Services",
    "2077": "Ambulance Services",
    "2081": "Hospitals",
    "2091": "Nursing Homes and Residential Care Facilities",
    "2112": "Services for the Elderly and Disabled",
    "2115": "Community Services",
    "2122": "Emergency and Relief Services",
    "2125": "Vocational Rehabilitation Services",
    "2128": "Child Day Care Services",
    "2130": "Performing Arts and Spectator Sports",
    "2133": "Theater Companies",
    "2135": "Dance Companies",
    "2139": "Circuses and Magic Shows",
    "2142": "Sports Teams and Clubs",
    "2143": "Racetracks",
    "2159": "Museums",
    "2161": "Historical Sites",
    "2163": "Zoos and Botanical Gardens",
    "2167": "Amusement Parks and Arcades",
    "2179": "Golf Courses and Country Clubs",
    "2181": "Skiing Facilities",
    "2190": "Accommodation Services",
    "2194": "Hotels and Motels",
    "2197": "Bed-and-Breakfasts, Hostels, Homestays",
    "2212": "Caterers",
    "2214": "Mobile Food Services",
    "2217": "Bars, Taverns, and Nightclubs",
    "2225": "Repair and Maintenance",
    "2226": "Vehicle Repair and Maintenance",
    "2240": "Electronic and Precision Equipment Maintenance",
    "2247": "Commercial and Industrial Machinery Maintenance",
    "2253": "Reupholstery and Furniture Repair",
    "2255": "Footwear and Leather Goods Repair",
    "2258": "Personal and Laundry Services",
    "2259": "Personal Care Services",
    "2272": "Laundry and Drycleaning Services",
    "2282": "Pet Services",
    "2318": "Household Services",
    "2353": "Health and Human Services",
    "2358": "Public Health",
    "2360": "Public Assistance Programs",
    "2366": "Air, Water, and Waste Program Management",
    "2368": "Conservation Programs",
    "2369": "Housing and Community Development",
    "2374": "Community Development and Urban Planning",
    "2375": "Economic Programs",
    "2391": "Military and International Affairs",
    "2401": "Operations Consulting",
    "2458": "Data Infrastructure and Analytics",
    "2468": "Electrical Equipment Manufacturing",
    "2489": "Wind Electric Power Generation",
    "2500": "Wineries",
    "2934": "Landscaping Services",
    "3065": "Courts of Law",
    "3068": "Correctional Institutions",
    "3070": "Fire Protection",
    "3081": "Housing Programs",
    "3085": "Transportation Programs",
    "3086": "Utilities Administration",
    "3089": "Space Research and Technology",
    "3095": "Oil Extraction",
    "3096": "Natural Gas Extraction",
    "3099": "Embedded Software Products",
    "3100": "Mobile Computing Software Products",
    "3101": "Desktop Computing Software Products",
    "3102": "IT System Custom Software Development",
    "3103": "IT System Operations and Maintenance",
    "3104": "IT System Installation and Disposal",
    "3105": "IT System Training and Support",
    "3106": "IT System Data Services",
    "3107": "IT System Testing and Evaluation",
    "3124": "Internet News",
    "3125": "Blogs",
    "3126": "Interior Design",
    "3127": "Social Networking Platforms",
    "3128": "Business Intelligence Platforms",
    "3129": "Business Content",
    "3130": "Data Security Software Products",
    "3131": "Mobile Gaming Apps",
    "3132": "Internet Publishing",
    "3133": "Media & Telecommunications",
    "3134": "Blockchain Services",
    "3186": "Retail Art Dealers",
    "3240": "Renewable Energy Power Generation",
    "3241": "Renewable Energy Equipment Manufacturing",
    "3242": "Engineering Services",
    "3243": "Services for Renewable Energy",
    "3244": "Digital Accessibility Services",
    "3245": "Accessible Hardware Manufacturing",
    "3246": "Accessible Architecture and Design",
    "3247": "Robot Manufacturing",
    "3248": "Robotics Engineering",
    "3249": "Surveying and Mapping Services",
    "3250": "Retail Pharmacies",
    "3251": "Climate Technology Product Manufacturing",
    "3252": "Climate Data and Analytics",
    "3253": "Alternative Fuel Vehicle Manufacturing",
    "3254": "Smart Meter Manufacturing",
    "3255": "Fuel Cell Manufacturing",
    "3256": "Regenerative Design",
}


def _resolve_geo(geo_urns):
    if not geo_urns:
        return 'Global'
    names = list(dict.fromkeys(GEO_MAP.get(u, u.split(':')[-1]) for u in geo_urns))
    if set(names) == {'US', 'Canada'}:
        return 'US, Canada'
    return ', '.join(names)


def _format_company_size(val):
    m = re.match(r'SIZE_(\d+)_TO_(\d+)', val)
    if m:
        return f'{int(m.group(1)):,} - {int(m.group(2)):,}'
    m2 = re.match(r'SIZE_(\d+)_OR_MORE', val)
    if m2:
        return f'{int(m2.group(1)):,}+'
    m3 = re.match(r'SIZE_(\d+)', val)
    if m3:
        return f'{int(m3.group(1)):,}'
    return val


class LinkedInClient:
    """Client for LinkedIn Marketing API."""

    def __init__(self, access_token, account_id, rate_limit_delay=0.2, max_retries=2):
        self.access_token = access_token
        self.account_id = account_id
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self._request_count = 0

    @property
    def _rest_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'LinkedIn-Version': '202503',
            'X-Restli-Protocol-Version': '2.0.0',
        }

    @property
    def _v2_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        }

    def _api_get(self, url, headers, retries=None):
        if retries is None:
            retries = self.max_retries
        for attempt in range(retries + 1):
            try:
                self._request_count += 1
                resp = requests.get(url, headers=headers, timeout=30)
                if resp.status_code == 401:
                    raise LinkedInAuthError(
                        f"Authentication failed (401) for {url[:80]}. "
                        "Your access token may be expired or invalid.",
                        response=resp,
                    )
                if resp.status_code == 429:
                    wait = float(resp.headers.get('Retry-After', 5))
                    logger.warning("Rate limited, waiting %ss...", wait)
                    if attempt >= retries:
                        raise LinkedInRateLimitError(
                            f"Rate limit exceeded after {retries + 1} attempts for {url[:80]}.",
                            retry_after=wait,
                            response=resp,
                        )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
            except (LinkedInAuthError, LinkedInRateLimitError):
                raise
            except Exception as e:
                if attempt < retries:
                    logger.info("API request attempt %d failed, retrying: %s", attempt + 1, e)
                    time.sleep(0.5 * (attempt + 1))
                    continue
                logger.error("API error (%s...): %s", url[:80], e)
                return None
        return None

    def _throttle(self):
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    # ─── Campaign Listing ─────────────────────────────────────────────────

    def list_campaigns(self, status_filter=None):
        """Fetch all campaigns from the ad account.
        status_filter: None for all, 'ACTIVE' for active only.
        Returns list of campaign dicts with id and metadata.
        """
        url = (
            f"{LINKEDIN_API_BASE}/rest/adAccounts/{self.account_id}"
            f"/adCampaigns?q=search&count=100"
        )
        data = self._api_get(url, self._rest_headers)
        if not data or 'elements' not in data:
            return []
        campaigns = data['elements']
        if status_filter:
            campaigns = [c for c in campaigns if c.get('status') == status_filter]
        # Filter out REMOVED campaigns
        campaigns = [c for c in campaigns if c.get('status') != 'REMOVED']
        return campaigns

    def get_campaign_ids(self, campaigns_arg):
        """Parse the --campaigns argument and return list of campaign ID strings.
        campaigns_arg: 'all', 'active', or comma-separated IDs like '123,456'
        """
        if campaigns_arg.lower() == 'all':
            camps = self.list_campaigns()
            return [str(c.get('id', c.get('campaignId', ''))) for c in camps]
        elif campaigns_arg.lower() == 'active':
            camps = self.list_campaigns(status_filter='ACTIVE')
            return [str(c.get('id', c.get('campaignId', ''))) for c in camps]
        else:
            return [cid.strip() for cid in campaigns_arg.split(',') if cid.strip()]

    # ─── Campaign Details ─────────────────────────────────────────────────

    def get_campaign_detail(self, campaign_id):
        url = (
            f"{LINKEDIN_API_BASE}/rest/adAccounts/{self.account_id}"
            f"/adCampaigns/{campaign_id}"
        )
        return self._api_get(url, self._rest_headers)

    # ─── Analytics ────────────────────────────────────────────────────────

    def _build_date_range(self, start_dt, end_dt):
        return (
            f"(start:(year:{start_dt.year},month:{start_dt.month},"
            f"day:{start_dt.day}),end:(year:{end_dt.year},"
            f"month:{end_dt.month},day:{end_dt.day}))"
        )

    def fetch_analytics_batch1(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})&fields={FIELDS_BATCH1}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_analytics_batch2(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})&fields={FIELDS_BATCH2}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_analytics_batch3(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})&fields={FIELDS_BATCH3}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_analytics_batch4(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})&fields={FIELDS_BATCH4}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_analytics_batch5(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})&fields={FIELDS_BATCH5}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_extra_pivot_analytics(self, campaign_id, date_range, pivot):
        """Fetch analytics for non-demographic pivots like device type."""
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot={pivot}&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})"
            f"&fields=impressions,clicks,costInUsd,pivotValues&count=25"
        )
        return self._api_get(url, self._v2_headers)

    def _parse_extra_pivot(self, data):
        """Parse extra pivot API response into a list of dicts."""
        elements = (data or {}).get('elements', [])
        result = []
        for el in elements:
            pvs = el.get('pivotValues', [])
            name = pvs[0] if pvs else 'Unknown'
            # Clean up URN-style names
            if ':' in name:
                name = name.split(':')[-1]
            result.append({
                'name': name,
                'impressions': el.get('impressions', 0),
                'clicks': el.get('clicks', 0),
                'cost': float(el.get('costInUsd', '0') or 0),
            })
        return result

    def fetch_creative_analytics(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CREATIVE&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})"
            f"&fields=impressions,clicks,totalEngagements,pivotValues&count=25"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_monthly_trends(self, campaign_id, date_range):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot=CAMPAIGN&dateRange={date_range}&timeGranularity=MONTHLY"
            f"&campaigns=List({urn})&fields={MONTHLY_FIELDS}"
        )
        return self._api_get(url, self._v2_headers)

    def fetch_demographics(self, campaign_id, date_range, pivot):
        urn = f"urn%3Ali%3AsponsoredCampaign%3A{campaign_id}"
        url = (
            f"{LINKEDIN_API_BASE}/v2/adAnalyticsV2?q=analytics"
            f"&pivot={pivot}&dateRange={date_range}&timeGranularity=ALL"
            f"&campaigns=List({urn})"
            f"&fields=impressions,clicks,pivotValues&count=25"
        )
        return self._api_get(url, self._v2_headers)

    # ─── Creative Details + Images ────────────────────────────────────────

    def get_creative(self, creative_urn):
        encoded = requests.utils.quote(creative_urn, safe='')
        url = (
            f"{LINKEDIN_API_BASE}/rest/adAccounts/{self.account_id}"
            f"/creatives/{encoded}"
        )
        return self._api_get(url, self._rest_headers)

    def get_share(self, share_id):
        url = f"{LINKEDIN_API_BASE}/v2/shares/{share_id}"
        return self._api_get(url, self._v2_headers)

    def get_creative_image_url(self, creative_data):
        if not creative_data or not creative_data.get('content', {}).get('reference'):
            return None
        share_id = creative_data['content']['reference'].split(':')[-1]
        share_data = self.get_share(share_id)
        if not share_data:
            return None
        entities = share_data.get('content', {}).get('contentEntities', [])
        if entities:
            thumbnails = entities[0].get('thumbnails', [])
            if thumbnails:
                return thumbnails[0].get('resolvedUrl')
        return None

    # ─── Name Resolution (batch and individual) ──────────────────────────

    def batch_resolve_orgs(self, org_ids):
        result = {}
        ids = list(org_ids)
        for i in range(0, len(ids), 20):
            chunk = ids[i:i + 20]
            id_list = ','.join(chunk)
            url = f"{LINKEDIN_API_BASE}/rest/organizationsLookup?ids=List({id_list})"
            data = self._api_get(url, self._rest_headers)
            if data and 'results' in data:
                for oid, val in data['results'].items():
                    result[f'urn:li:organization:{oid}'] = (
                        val.get('localizedName') or f'Company #{oid}'
                    )
            for oid in chunk:
                key = f'urn:li:organization:{oid}'
                if key not in result:
                    result[key] = f'Company #{oid}'
            self._throttle()
        return result

    def batch_resolve_titles(self, title_ids):
        result = {}
        ids = list(title_ids)
        for i in range(0, len(ids), 20):
            chunk = ids[i:i + 20]
            url = f"{LINKEDIN_API_BASE}/v2/titles?ids=List({','.join(chunk)})"
            data = self._api_get(url, self._v2_headers)
            if data and 'results' in data:
                for tid, val in data['results'].items():
                    name = (val.get('name', {}).get('localized', {}).get('en_US')
                            or str(tid))
                    result[f'urn:li:title:{tid}'] = name
            self._throttle()
        return result

    def batch_resolve_industries(self, industry_ids):
        result = {}
        ids = list(industry_ids)
        # First populate from static v2 map
        for iid in ids:
            if iid in INDUSTRY_V2:
                result[f'urn:li:industry:{iid}'] = INDUSTRY_V2[iid]
        # Then try API for remaining (standard IDs 1-148)
        unresolved = [iid for iid in ids if f'urn:li:industry:{iid}' not in result]
        for i in range(0, len(unresolved), 20):
            chunk = unresolved[i:i + 20]
            url = f"{LINKEDIN_API_BASE}/v2/industries?ids=List({','.join(chunk)})"
            data = self._api_get(url, self._v2_headers)
            if data and 'results' in data:
                for iid, val in data['results'].items():
                    name = (val.get('name', {}).get('localized', {}).get('en_US')
                            or str(iid))
                    result[f'urn:li:industry:{iid}'] = name
            self._throttle()
        return result

    def batch_resolve_geo(self, geo_ids):
        result = {}
        ids = list(geo_ids)
        for i in range(0, len(ids), 20):
            chunk = ids[i:i + 20]
            url = f"{LINKEDIN_API_BASE}/v2/geo?ids=List({','.join(chunk)})"
            data = self._api_get(url, self._v2_headers)
            if data and 'results' in data:
                for gid, val in data['results'].items():
                    result[f'urn:li:geo:{gid}'] = (
                        val.get('defaultLocalizedName', {}).get('value') or str(gid)
                    )
            self._throttle()
        return result

    def resolve_function(self, func_id):
        url = f"{LINKEDIN_API_BASE}/v2/functions/{func_id}"
        data = self._api_get(url, self._v2_headers)
        if data:
            return data.get('name', {}).get('localized', {}).get('en_US') or str(func_id)
        return str(func_id)

    def resolve_seniority(self, sen_id):
        url = f"{LINKEDIN_API_BASE}/v2/seniorities/{sen_id}"
        data = self._api_get(url, self._v2_headers)
        if data:
            return data.get('name', {}).get('localized', {}).get('en_US') or str(sen_id)
        return str(sen_id)

    # ─── Full Data Fetch (mirrors n8n "Fetch All Campaign Data") ─────────

    def fetch_all_campaign_data(self, campaign_ids, progress_callback=None):
        """Fetch complete data for all campaigns, including analytics,
        demographics, creatives, and resolved names.
        Returns dict with 'campaigns' and 'report_date' keys.
        """
        from datetime import datetime

        def log(msg):
            if progress_callback:
                progress_callback(msg)
            else:
                print(msg)

        log(f"Fetching {len(campaign_ids)} campaigns...")

        # STEP 1: Fetch campaign details
        valid_campaigns = []
        for cid in campaign_ids:
            camp_data = self.get_campaign_detail(cid)
            if not camp_data:
                log(f"  Skipping campaign {cid} (no data)")
                continue

            start_ms = 0
            run_schedule = camp_data.get('runSchedule', {})
            if run_schedule:
                start_ms = run_schedule.get('start', 0)
            start_dt = (datetime.fromtimestamp(start_ms / 1000)
                        if start_ms else datetime(2025, 1, 1))

            geo_urns = []
            targeting = camp_data.get('targetingCriteria', {})
            for clause in targeting.get('include', {}).get('and', []):
                if 'or' in clause:
                    for key, vals in clause['or'].items():
                        kl = key.lower()
                        if 'geo' in kl or 'location' in kl or 'country' in kl:
                            geo_urns.extend(vals)

            display_name = camp_data.get('name', f'Campaign {cid}')
            nm = display_name.split('-')[0].strip()
            if nm and len(nm) < len(display_name) and len(nm) > 2:
                display_name = nm

            now = datetime.now()
            dr = self._build_date_range(start_dt, now)

            valid_campaigns.append({
                'campId': str(cid),
                'campData': camp_data,
                'startMs': start_ms,
                'startDt': start_dt,
                'geoUrns': geo_urns,
                'displayName': display_name,
                'dr': dr,
            })
            self._throttle()

        log(f"{len(valid_campaigns)} valid campaigns. Fetching analytics + demographics...")

        # STEP 2: Fetch analytics + demographics per campaign
        all_results = []
        for vc in valid_campaigns:
            cid = vc['campId']
            dr = vc['dr']

            batch1 = self.fetch_analytics_batch1(cid, dr)
            batch2 = self.fetch_analytics_batch2(cid, dr)

            # Batches 3-5: wrap in try/except as some fields may not be
            # available for older API versions or certain campaign types.
            try:
                batch3 = self.fetch_analytics_batch3(cid, dr)
            except Exception as e:
                logger.warning("Batch3 failed for campaign %s: %s", cid, e)
                batch3 = None
            try:
                batch4 = self.fetch_analytics_batch4(cid, dr)
            except Exception as e:
                logger.warning("Batch4 failed for campaign %s: %s", cid, e)
                batch4 = None
            try:
                batch5 = self.fetch_analytics_batch5(cid, dr)
            except Exception as e:
                logger.warning("Batch5 failed for campaign %s: %s", cid, e)
                batch5 = None

            cr_analytics = self.fetch_creative_analytics(cid, dr)
            monthly_data = self.fetch_monthly_trends(cid, dr)

            demo_results = {}
            for pivot in PIVOTS:
                demo_results[pivot] = self.fetch_demographics(cid, dr, pivot)
                self._throttle()

            # Extra pivots (device type, serving location)
            extra_pivot_results = {}
            for pivot in EXTRA_PIVOTS:
                try:
                    extra_pivot_results[pivot] = self.fetch_extra_pivot_analytics(cid, dr, pivot)
                except Exception as e:
                    logger.warning("Extra pivot %s failed for campaign %s: %s", pivot, cid, e)
                    extra_pivot_results[pivot] = None
                self._throttle()

            # Merge analytics batches (safely handle empty element lists)
            def _first_element(batch):
                if not batch:
                    return {}
                elements = batch.get('elements', [])
                return elements[0] if elements else {}

            stats1 = _first_element(batch1)
            stats2 = _first_element(batch2)
            stats3 = _first_element(batch3)
            stats4 = _first_element(batch4)
            stats5 = _first_element(batch5)
            merged = {**stats1, **stats2, **stats3, **stats4, **stats5}

            # Parse monthly trends
            # LinkedIn v2 API with timeGranularity=MONTHLY returns elements
            # in chronological order but without dateRange in each element.
            # We compute months from the campaign start date + element index.
            monthly_trends = []
            monthly_elements = (monthly_data or {}).get('elements', [])
            for idx, el in enumerate(monthly_elements):
                # Try dateRange first (some API versions include it)
                s = el.get('dateRange', {}).get('start', {})
                if s and s.get('year') and s.get('month'):
                    month_idx = s['month'] - 1
                    year = s['year']
                else:
                    # Compute from start date + index
                    camp_start = vc['startDt']
                    total_months = camp_start.month - 1 + idx
                    year = camp_start.year + total_months // 12
                    month_idx = total_months % 12
                if 0 <= month_idx < 12:
                    month_label = f"{MONTH_NAMES[month_idx]} {year}"
                else:
                    month_label = 'Unknown'
                monthly_trends.append({
                    'month': month_label,
                    'impressions': el.get('impressions', 0),
                    'clicks': el.get('clicks', 0),
                    'cost': float(el.get('costInUsd', '0') or 0),
                    'engagements': el.get('totalEngagements', 0),
                })

            def _month_sort_key(m):
                parts = m['month'].split(' ')
                if len(parts) == 2 and parts[0] in MONTH_NAMES:
                    return int(parts[1]) * 100 + MONTH_NAMES.index(parts[0])
                return 0

            monthly_trends.sort(key=_month_sort_key)

            all_results.append({
                'analytics': merged,
                'crAnalytics': cr_analytics,
                'demoResults': demo_results,
                'monthlyTrends': monthly_trends,
                'extraPivots': extra_pivot_results,
            })
            log(f"  {vc['displayName']}: analytics fetched")

        log("Analytics done. Fetching creative details + resolving demographics...")

        # STEP 3: Build campaign objects
        campaigns = []
        for idx, vc in enumerate(valid_campaigns):
            cid = vc['campId']
            camp_data = vc['campData']
            result = all_results[idx]
            stats = result['analytics']
            cr_analytics = result['crAnalytics']

            # Creative details
            cr_stats = sorted(
                (cr_analytics or {}).get('elements', []),
                key=lambda x: x.get('impressions', 0),
                reverse=True,
            )
            cr_entries = [
                cs for cs in cr_stats[:10]
                if cs.get('pivotValues') and cs['pivotValues'][0]
            ]

            creatives = []
            for cs in cr_entries:
                cr_urn = cs['pivotValues'][0]
                cr_data = self.get_creative(cr_urn)
                image_url = self.get_creative_image_url(cr_data)
                creatives.append({
                    'id': cr_urn.split(':')[-1],
                    'name': (cr_data or {}).get('name', f"Creative {cr_urn.split(':')[-1]}"),
                    'impressions': cs.get('impressions', 0),
                    'clicks': cs.get('clicks', 0),
                    'image_url': image_url,
                })
                self._throttle()

            # Demographics
            camp_demo = {}
            for pivot in PIVOTS:
                demo_data = result['demoResults'].get(pivot)
                if demo_data and 'elements' in demo_data:
                    entries = []
                    for el in demo_data['elements']:
                        pv = (el.get('pivotValues') or ['Unknown'])[0]
                        entries.append({
                            'pivotValue': pv,
                            'impressions': el.get('impressions', 0),
                            'clicks': el.get('clicks', 0),
                        })
                    entries.sort(key=lambda x: x['impressions'], reverse=True)
                    camp_demo[pivot] = entries

            imp = stats.get('impressions') or 0
            clk = stats.get('clicks') or 0
            eng = stats.get('totalEngagements') or 0
            cost_usd = float(stats.get('costInUsd', '0') or 0) or None

            # Variables for derived metrics
            viral_imp = stats.get('viralImpressions', 0) or 0
            unique_imp = stats.get('approximateUniqueImpressions', 0) or 0
            video_views = stats.get('videoViews', 0) or 0
            video_comp = stats.get('videoCompletions', 0) or 0
            leads = stats.get('oneClickLeads', 0) or 0
            form_opens = stats.get('oneClickLeadFormOpens', 0) or 0
            sends_val = stats.get('sends', 0) or 0
            opens_val = stats.get('opens', 0) or 0
            cost = float(stats.get('costInUsd', '0') or 0)

            # Parse extra pivot data
            extra_pivots = result.get('extraPivots', {})
            device_breakdown = self._parse_extra_pivot(extra_pivots.get('IMPRESSION_DEVICE_TYPE'))
            serving_location = self._parse_extra_pivot(extra_pivots.get('SERVING_LOCATION'))

            obj_type = camp_data.get('objectiveType', '')
            camp_type = CAMPAIGN_TYPE_MAP.get(
                obj_type,
                obj_type.replace('_', ' ') if obj_type else 'N/A'
            )

            campaign_obj = {
                'id': cid,
                'name': camp_data.get('name', ''),
                'display_name': vc['displayName'],
                'campaign_type': camp_type,
                'status': camp_data.get('status', ''),
                'start_date': (
                    vc['startDt'].strftime('%Y-%m-%d') if vc['startMs'] else None
                ),
                'geo_urns': vc['geoUrns'],
                'geo_display': _resolve_geo(vc['geoUrns']),
                'impressions': imp,
                'clicks': clk,
                'engagements': eng,
                'likes': stats.get('likes'),
                'reactions': stats.get('reactions'),
                'comments': stats.get('comments'),
                'shares': stats.get('shares'),
                'follows': stats.get('follows'),
                'cost_usd': cost_usd,
                'landing_page_clicks': stats.get('landingPageClicks'),
                'company_page_clicks': stats.get('companyPageClicks'),
                'other_engagements': stats.get('otherEngagements'),
                'conversions': stats.get('externalWebsiteConversions'),
                'one_click_leads': stats.get('oneClickLeads'),
                'video_views': stats.get('videoViews'),
                'video_completions': stats.get('videoCompletions'),
                'video_first_quartile': stats.get('videoFirstQuartileCompletions'),
                'video_midpoint': stats.get('videoMidpointCompletions'),
                'video_third_quartile': stats.get('videoThirdQuartileCompletions'),
                'full_screen_plays': stats.get('fullScreenPlays'),
                'ctr': (clk / imp * 100) if clk and imp else None,
                'cpc': (cost_usd / clk) if cost_usd and clk else None,
                'cpm': (cost_usd / imp * 1000) if cost_usd and imp else None,
                'cost_per_engagement': (
                    (cost_usd / eng) if cost_usd and eng else None
                ),
                'engagement_rate': (eng / imp * 100) if eng and imp else None,

                # Viral metrics
                'viral_impressions': stats.get('viralImpressions', 0),
                'viral_clicks': stats.get('viralClicks', 0),
                'viral_likes': stats.get('viralLikes', 0),
                'viral_comments': stats.get('viralComments', 0),
                'viral_shares': stats.get('viralShares', 0),
                'viral_follows': stats.get('viralFollows', 0),
                'viral_reactions': stats.get('viralReactions', 0),
                'viral_total_engagements': stats.get('viralTotalEngagements', 0),
                'viral_landing_page_clicks': stats.get('viralLandingPageClicks', 0),
                'viral_company_page_clicks': stats.get('viralCompanyPageClicks', 0),
                'viral_other_engagements': stats.get('viralOtherEngagements', 0),
                'viral_conversions': stats.get('viralExternalWebsiteConversions', 0),
                'viral_one_click_leads': stats.get('viralOneClickLeads', 0),
                'viral_video_views': stats.get('viralVideoViews', 0),
                'viral_video_completions': stats.get('viralVideoCompletions', 0),

                # Lead gen metrics
                'one_click_lead_form_opens': stats.get('oneClickLeadFormOpens', 0),
                'qualified_leads': stats.get('qualifiedLeads', 0),
                'valid_work_email_leads': stats.get('validWorkEmailLeads', 0),
                'talent_leads': stats.get('talentLeads', 0),
                'lead_gen_mail_contact_shares': stats.get('leadGenerationMailContactInfoShares', 0),
                'lead_gen_mail_interested_clicks': stats.get('leadGenerationMailInterestedClicks', 0),
                'cost_per_qualified_lead': float(stats.get('costPerQualifiedLead', '0') or 0),
                'appointments_scheduled': stats.get('appointmentsScheduled', 0),

                # Messaging metrics
                'sends': stats.get('sends', 0),
                'opens': stats.get('opens', 0),
                'text_url_clicks': stats.get('textUrlClicks', 0),
                'action_clicks': stats.get('actionClicks', 0),
                'ad_unit_clicks': stats.get('adUnitClicks', 0),
                'headline_clicks': stats.get('headlineClicks', 0),
                'headline_impressions': stats.get('headlineImpressions', 0),

                # Conversion details
                'post_click_conversions': stats.get('externalWebsitePostClickConversions', 0),
                'post_view_conversions': stats.get('externalWebsitePostViewConversions', 0),
                'conversion_value_local': float(stats.get('conversionValueInLocalCurrency', '0') or 0),
                'job_applications': float(stats.get('jobApplications', '0') or 0),
                'job_apply_clicks': float(stats.get('jobApplyClicks', '0') or 0),
                'registrations': float(stats.get('registrations', '0') or 0),

                # Cost
                'cost_in_local_currency': float(stats.get('costInLocalCurrency', '0') or 0),

                # Document ads
                'document_completions': stats.get('documentCompletions', 0),
                'document_first_quartile': stats.get('documentFirstQuartileCompletions', 0),
                'document_midpoint': stats.get('documentMidpointCompletions', 0),
                'document_third_quartile': stats.get('documentThirdQuartileCompletions', 0),
                'download_clicks': stats.get('downloadClicks', 0),

                # Video extended
                'video_starts': stats.get('videoStarts', 0),
                'video_watch_time': stats.get('videoWatchTime', 0),
                'average_video_watch_time': float(stats.get('averageVideoWatchTime', '0') or 0),
                'average_dwell_time': stats.get('averageDwellTime', 0),

                # Engagement extended
                'comment_likes': stats.get('commentLikes', 0),
                'subscription_clicks': stats.get('subscriptionClicks', 0),

                # Event metrics
                'event_views': stats.get('eventViews', 0),
                'event_watch_time': stats.get('eventWatchTime', 0),

                # Derived metrics
                'viral_amplification_rate': round(viral_imp / imp * 100, 2) if imp > 0 else 0,
                'frequency': round(imp / unique_imp, 2) if unique_imp > 0 else 0,
                'video_view_rate': round(video_views / imp * 100, 2) if imp > 0 and video_views > 0 else 0,
                'video_completion_rate': round(video_comp / video_views * 100, 2) if video_views > 0 else 0,
                'lead_form_conversion_rate': round(leads / form_opens * 100, 2) if form_opens > 0 else 0,
                'open_rate': round(opens_val / sends_val * 100, 2) if sends_val > 0 else 0,

                # Extra pivot data
                'device_breakdown': device_breakdown,
                'serving_location': serving_location,

                'monthly_trends': result['monthlyTrends'],
                'creatives': creatives,
                'demographics': camp_demo,
            }
            campaigns.append(campaign_obj)
            log(f"  {vc['displayName']}: {imp or 0} imp, {len(creatives)} creatives")

        # STEP 4: Collect unique IDs for batch resolution
        all_title_ids = set()
        all_function_ids = set()
        all_industry_ids = set()
        all_geo_ids = set()
        all_org_ids = set()

        for camp in campaigns:
            demo = camp['demographics']
            for d in demo.get('MEMBER_JOB_TITLE', []):
                all_title_ids.add(d['pivotValue'].split(':')[-1])
            for d in demo.get('MEMBER_JOB_FUNCTION', []):
                all_function_ids.add(d['pivotValue'].split(':')[-1])
            for d in demo.get('MEMBER_INDUSTRY', []):
                all_industry_ids.add(d['pivotValue'].split(':')[-1])
            for d in demo.get('MEMBER_REGION_V2', []):
                all_geo_ids.add(d['pivotValue'].split(':')[-1])
            for d in demo.get('MEMBER_COUNTRY_V2', []):
                all_geo_ids.add(d['pivotValue'].split(':')[-1])
            for d in demo.get('MEMBER_COMPANY', []):
                if 'organization' in d['pivotValue']:
                    all_org_ids.add(d['pivotValue'].split(':')[-1])

        log(f"Resolving: {len(all_title_ids)} titles, {len(all_function_ids)} functions, "
            f"{len(all_industry_ids)} industries, {len(all_geo_ids)} geos, "
            f"{len(all_org_ids)} orgs")

        # Batch resolve
        title_map = self.batch_resolve_titles(all_title_ids) if all_title_ids else {}
        industry_map = self.batch_resolve_industries(all_industry_ids) if all_industry_ids else {}
        geo_map = self.batch_resolve_geo(all_geo_ids) if all_geo_ids else {}
        org_map = self.batch_resolve_orgs(all_org_ids) if all_org_ids else {}

        # Resolve functions individually
        function_map = {}
        for fid in all_function_ids:
            function_map[f'urn:li:function:{fid}'] = self.resolve_function(fid)
            self._throttle()

        # Resolve seniorities
        seniority_map = dict(SENIORITY_MAP)
        unresolved_seniorities = set()
        for camp in campaigns:
            for d in camp['demographics'].get('MEMBER_SENIORITY', []):
                if d['pivotValue'] not in seniority_map:
                    unresolved_seniorities.add(d['pivotValue'].split(':')[-1])
        for sid in unresolved_seniorities:
            name = self.resolve_seniority(sid)
            seniority_map[f'urn:li:seniority:{sid}'] = name
            self._throttle()

        # STEP 5: Apply resolved names
        for camp in campaigns:
            demo = camp['demographics']
            if 'MEMBER_JOB_TITLE' in demo:
                for d in demo['MEMBER_JOB_TITLE']:
                    d['displayName'] = title_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_JOB_FUNCTION' in demo:
                for d in demo['MEMBER_JOB_FUNCTION']:
                    d['displayName'] = function_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_INDUSTRY' in demo:
                for d in demo['MEMBER_INDUSTRY']:
                    iid = d['pivotValue'].split(':')[-1]
                    d['displayName'] = industry_map.get(
                        d['pivotValue'], f'Industry #{iid}')
            if 'MEMBER_REGION_V2' in demo:
                for d in demo['MEMBER_REGION_V2']:
                    d['displayName'] = geo_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_COUNTRY_V2' in demo:
                for d in demo['MEMBER_COUNTRY_V2']:
                    d['displayName'] = geo_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_COMPANY' in demo:
                for d in demo['MEMBER_COMPANY']:
                    d['displayName'] = org_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_SENIORITY' in demo:
                for d in demo['MEMBER_SENIORITY']:
                    d['displayName'] = seniority_map.get(
                        d['pivotValue'], d['pivotValue'].split(':')[-1])
            if 'MEMBER_COMPANY_SIZE' in demo:
                for d in demo['MEMBER_COMPANY_SIZE']:
                    d['displayName'] = _format_company_size(d['pivotValue'])

        report_date = datetime.now().strftime('%d-%m-%Y')
        log(f"Done! {len(campaigns)} campaigns processed with resolved demographics.")

        return {
            'campaigns': campaigns,
            'report_date': report_date,
        }
