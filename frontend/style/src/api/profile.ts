import axios from '@/utils/axios';

export type ProfilePayload = {
  first_name?: string;
  last_name?: string;
  phone?: string;
  address?: string;
  address2?: string;
  city?: string;
  country?: string;
  zip_code?: string;
  company_name?: string;
  vat_id?: string;
  company_url?: string;
  business_category?: string;
  organization_size?: string;
  interest_category?: string;
};

export async function getProfile() {
  const { data } = await axios.get('/accounts/profile/');
  return data;
}

export async function updateProfile(payload: ProfilePayload) {
  const { data } = await axios.post('/accounts/profile/', payload);
  return data;
}
