const input = $input.first().json;
const body = input.body && typeof input.body === 'object' ? input.body : input;

const firstValue = (...values) =>
  values.find((value) => value !== undefined && value !== null && String(value).trim() !== '');

const clean = (value) => {
  if (value === undefined || value === null) return null;
  return typeof value === 'string' ? value.trim() || null : value;
};

const data = {
  name: clean(firstValue(body.name, body.full_name, body.fullName)),
  email: clean(firstValue(body.email, body.email_address, body.emailAddress)),
  phone: clean(firstValue(body.phone, body.phone_number, body.phoneNumber)),
  company: clean(firstValue(body.company, body.business, body.business_name, body.businessName)),
  message: clean(firstValue(body.message, body.notes, body.details)),
};

if (typeof data.email === 'string') data.email = data.email.toLowerCase();

const errors = [];
for (const field of ['name', 'email']) {
  if (!data[field]) errors.push({ field, code: 'required', message: field + ' is required' });
}

if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
  errors.push({ field: 'email', code: 'invalid_email', message: 'email must be a valid address' });
}

if (data.message && data.message.length > 2000) {
  errors.push({ field: 'message', code: 'too_long', message: 'message must be 2000 characters or fewer' });
}

const ok = errors.length === 0;

return [{
  json: {
    ok,
    statusCode: ok ? 200 : 422,
    data,
    errors,
    meta: { validatedAt: new Date().toISOString() },
  },
}];
