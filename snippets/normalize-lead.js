const input = $input.first().json;
const body = input.body && typeof input.body === 'object' ? input.body : input;

const firstValue = (...values) =>
  values.find((value) => value !== undefined && value !== null && String(value).trim() !== '');

const clean = (value) => {
  if (value === undefined || value === null) return null;
  return typeof value === 'string' ? value.trim() || null : value;
};

const email = clean(firstValue(body.email, body.email_address, body.emailAddress));
const phoneRaw = clean(firstValue(body.phone, body.phone_number, body.phoneNumber));
const phone = typeof phoneRaw === 'string' ? phoneRaw.replace(/[^+\d]/g, '') || null : phoneRaw;

return [{
  json: {
    lead: {
      fullName: clean(firstValue(body.full_name, body.fullName, body.name)),
      email: typeof email === 'string' ? email.toLowerCase() : email,
      phone,
      company: clean(firstValue(body.company, body.business, body.business_name, body.businessName)),
      website: clean(firstValue(body.website, body.url)),
      service: clean(firstValue(body.service, body.service_interest, body.serviceInterest)),
      message: clean(firstValue(body.message, body.notes, body.details)),
      source: clean(firstValue(body.source, body.lead_source, body.leadSource, body.utm_source)),
    },
    attribution: {
      utmSource: clean(firstValue(body.utm_source, body.utmSource)),
      utmMedium: clean(firstValue(body.utm_medium, body.utmMedium)),
      utmCampaign: clean(firstValue(body.utm_campaign, body.utmCampaign)),
      referrer: clean(firstValue(body.referrer, body.referer)),
    },
    meta: {
      receivedAt: new Date().toISOString(),
      originalKeys: Object.keys(body).sort(),
    },
  },
}];
