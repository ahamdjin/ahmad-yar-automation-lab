const input = $input.first().json;
const body = input.body && typeof input.body === 'object' ? input.body : input;
const query = input.query && typeof input.query === 'object' ? input.query : {};

const firstValue = (...values) =>
  values.find((value) => value !== undefined && value !== null && String(value).trim() !== '');

const text = (value, lower = false) => {
  if (value === undefined || value === null) return null;
  const cleaned = String(value).trim();
  if (!cleaned) return null;
  return lower ? cleaned.toLowerCase() : cleaned;
};

const pick = (...keys) => firstValue(...keys.flatMap((key) => [body[key], query[key]]));
const source = text(pick('utm_source', 'utmSource'), true);
const medium = text(pick('utm_medium', 'utmMedium'), true);
const campaign = text(pick('utm_campaign', 'utmCampaign'));
const term = text(pick('utm_term', 'utmTerm'));
const content = text(pick('utm_content', 'utmContent'));
const referrer = text(firstValue(body.referrer, body.referer, input.headers?.referer));
const landingPage = text(firstValue(body.landing_page, body.landingPage, body.url, query.url));
const gclid = text(pick('gclid'));
const fbclid = text(pick('fbclid'));

let canonicalLandingPage = landingPage;
if (landingPage) {
  try {
    const url = new URL(landingPage);
    for (const key of [...url.searchParams.keys()]) {
      if (key.toLowerCase().startsWith('utm_') || ['gclid', 'fbclid', 'msclkid'].includes(key.toLowerCase())) {
        url.searchParams.delete(key);
      }
    }
    canonicalLandingPage = url.toString();
  } catch {
    canonicalLandingPage = landingPage;
  }
}

const socialSources = ['facebook', 'instagram', 'linkedin', 'tiktok', 'x', 'twitter', 'youtube', 'pinterest'];
const searchSources = ['google', 'bing', 'duckduckgo', 'yahoo'];

let channel = 'direct';
if (gclid || /cpc|ppc|paid[-_ ]?search|sem/.test(medium || '')) channel = 'paid_search';
else if (/paid[-_ ]?social|social[-_ ]?paid/.test(medium || '') || (fbclid && socialSources.includes(source))) channel = 'paid_social';
else if (/email|newsletter/.test(medium || '') || /email|newsletter/.test(source || '')) channel = 'email';
else if (medium === 'organic' || searchSources.includes(source)) channel = 'organic_search';
else if (/social/.test(medium || '') || socialSources.includes(source)) channel = 'organic_social';
else if (referrer) channel = 'referral';
else if (source || medium) channel = 'other';

return [{
  json: {
    attribution: { source, medium, campaign, term, content, channel, gclid, fbclid, referrer },
    landingPage: { original: landingPage, canonical: canonicalLandingPage },
    meta: { processedAt: new Date().toISOString() },
  },
}];
