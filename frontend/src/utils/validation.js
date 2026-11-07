export const isRequired = (value) => String(value ?? '').trim().length > 0;
export const isEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value ?? '').trim());
export const isPhone = (value) => /^[0-9+()\-\s]{8,20}$/.test(String(value ?? '').trim());
export const isPositiveNumber = (value) => Number(value) > 0;
export const isFutureOrToday = (value) => {
  if (!value) return false;
  const selected = new Date(`${value}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return selected >= today;
};
export const minLength = (value, min) => String(value ?? '').trim().length >= min;

export function validateFiles(fileList, { imagesOnly = false, maxFiles = 8 } = {}) {
  const files = Array.from(fileList || []);
  if (files.length > maxFiles) return `Please upload no more than ${maxFiles} files.`;
  if (imagesOnly && files.some((file) => !file.type.startsWith('image/'))) {
    return 'Only image files are allowed.';
  }
  return '';
}
