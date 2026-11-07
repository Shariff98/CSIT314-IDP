export const demoAccounts = [
  { id: 1, name: 'Alicia Tan', email: 'customer@example.com', password: 'password123', role: 'customer', status: 'active' },
  { id: 2, name: 'Studio North', email: 'designer@example.com', password: 'password123', role: 'designer', status: 'active', designerId: 101 },
  { id: 3, name: 'Platform Admin', email: 'admin@example.com', password: 'password123', role: 'admin', status: 'active' },
  { id: 4, name: 'Platform Admin 2', email: 'admin2@example.com', password: 'password123', role: 'admin', status: 'active' },
  { id: 5, name: 'New Leaf Interior', email: 'pending@example.com', password: 'password123', role: 'designer', status: 'active', designerId: 104 },
  { id: 6, name: 'Marcus Lim', email: 'marcus@example.com', password: 'password123', role: 'customer', status: 'active' },
];

export const initialDesigners = [
  {
    id: 101,
    companyName: 'Studio North Interiors',
    registrationNo: '202612345N',
    contactEmail: 'hello@studionorth.example',
    phone: '+65 6123 4567',
    location: 'Central Singapore',
    rating: 4.8,
    reviewCount: 42,
    yearsExperience: 12,
    specialties: ['Modern', 'Minimalist', 'Scandinavian'],
    propertyTypes: ['HDB', 'Condo', 'Landed'],
    categoriesServed: ['Living Room', 'Kitchen', 'Bedroom', 'Whole Home'],
    services: ['Space Planning', 'Carpentry', 'Project Management'],
    budgetMin: 30000,
    budgetMax: 120000,
    description: 'A practical interior design studio focused on warm, functional homes with clean detailing.',
    verified: true,
    status: 'active',
    logo: '/studio-north.svg',
  },
  {
    id: 102,
    companyName: 'Oak & Form Design',
    registrationNo: '202645678K',
    contactEmail: 'team@oakform.example',
    phone: '+65 6234 7788',
    location: 'East Singapore',
    rating: 4.5,
    reviewCount: 31,
    yearsExperience: 8,
    specialties: ['Japandi', 'Contemporary', 'Natural'],
    propertyTypes: ['HDB', 'Condo'],
    categoriesServed: ['Kitchen', 'Living Room', 'Whole Home'],
    services: ['Interior Design', 'Renovation', 'Lighting Design'],
    budgetMin: 25000,
    budgetMax: 90000,
    description: 'Residential design studio using natural materials and calm palettes for everyday living.',
    verified: true,
    status: 'active',
    logo: '/oak-form.svg',
  },
  {
    id: 103,
    companyName: 'Bold Habitat',
    registrationNo: '202698765M',
    contactEmail: 'design@boldhabitat.example',
    phone: '+65 6345 9922',
    location: 'North Singapore',
    rating: 4.2,
    reviewCount: 19,
    yearsExperience: 6,
    specialties: ['Industrial', 'Eclectic', 'Modern'],
    propertyTypes: ['HDB', 'Landed'],
    categoriesServed: ['Office', 'Bedroom', 'Living Room'],
    services: ['Concept Design', 'Renovation', 'Styling'],
    budgetMin: 18000,
    budgetMax: 80000,
    description: 'Designs with stronger colours, expressive materials and space-saving built-ins.',
    verified: true,
    status: 'active',
    logo: '/bold-habitat.svg',
  },
  {
    id: 104,
    companyName: 'New Leaf Interior',
    registrationNo: '202611122Z',
    contactEmail: 'newleaf@example.com',
    phone: '+65 6777 1122',
    location: 'West Singapore',
    rating: 0,
    reviewCount: 0,
    yearsExperience: 4,
    specialties: ['Modern'],
    propertyTypes: ['HDB'],
    categoriesServed: ['Kitchen', 'Living Room'],
    services: ['Interior Design'],
    budgetMin: 20000,
    budgetMax: 70000,
    description: 'Newly registered company awaiting platform approval.',
    verified: false,
    status: 'pending',
    logo: '/new-leaf.svg',
  },
];

export const initialProjects = [
  { id: 201, designerId: 101, title: 'Scandinavian 4-Room HDB', description: 'Light timber finishes, concealed storage and a bright open living area.', category: 'Living Room', styles: ['Scandinavian', 'Minimalist'], propertyType: 'HDB', location: 'Tampines', budget: 58000, completionDate: '2026-08-12', published: true, views: 1284, photos: ['/project-living.svg', '/project-kitchen.svg'] },
  { id: 202, designerId: 101, title: 'Warm Minimalist Kitchen', description: 'A compact kitchen with quartz counters, warm lighting and tall pantry storage.', category: 'Kitchen', styles: ['Minimalist'], propertyType: 'Condo', location: 'Bishan', budget: 42000, completionDate: '2026-07-02', published: true, views: 837, photos: ['/project-kitchen.svg', '/project-detail.svg'] },
  { id: 203, designerId: 102, title: 'Japandi Family Home', description: 'Calm tones, rounded carpentry and flexible shared spaces for a young family.', category: 'Whole Home', styles: ['Japandi', 'Natural'], propertyType: 'HDB', location: 'Punggol', budget: 76000, completionDate: '2026-05-19', published: true, views: 654, photos: ['/project-bedroom.svg', '/project-living.svg'] },
  { id: 204, designerId: 103, title: 'Industrial Home Office', description: 'Dark metal details, open shelving and an acoustic work corner.', category: 'Office', styles: ['Industrial'], propertyType: 'HDB', location: 'Woodlands', budget: 25000, completionDate: '2026-09-01', published: true, views: 431, photos: ['/project-office.svg'] },
  { id: 205, designerId: 101, title: 'Compact Bedroom Storage', description: 'A platform bed with integrated storage and a compact study nook.', category: 'Bedroom', styles: ['Modern'], propertyType: 'Landed', location: 'Yishun', budget: 18000, completionDate: '2026-10-08', published: true, views: 298, photos: ['/project-bedroom.svg'] },
];

export const initialPackages = [
  { id: 301, designerId: 101, name: 'Essential Kitchen Refresh', renovationType: 'Kitchen', price: 28800, description: 'Carpentry, countertop, backsplash, lighting and project coordination.', services: ['Carpentry', 'Countertop', 'Lighting'] },
  { id: 302, designerId: 101, name: '4-Room Full Renovation', renovationType: 'Whole Home', price: 68800, description: 'Concept design plus full-home renovation for a typical 4-room flat.', services: ['Design', 'Carpentry', 'Electrical', 'Painting'] },
  { id: 303, designerId: 102, name: 'Japandi Living Package', renovationType: 'Living Room', price: 19800, description: 'Living room carpentry, feature wall, lighting plan and styling.', services: ['Design', 'Feature Wall', 'Lighting'] },
];

export const initialReviews = [
  { id: 401, designerId: 101, customerName: 'Alicia Tan', rating: 5, text: 'The team communicated clearly and the finished carpentry matched the proposal.', date: '2026-10-01', response: 'Thank you! We enjoyed working on your home.' },
  { id: 402, designerId: 102, customerName: 'Marcus Lim', rating: 4, text: 'Good design direction and helpful material recommendations.', date: '2026-09-14', response: '' },
  { id: 403, designerId: 103, customerName: 'Siti N.', rating: 4, text: 'Creative ideas and responsive during the renovation.', date: '2026-08-20', response: '' },
];

export const initialEnquiries = [
  {
    id: 501,
    customerName: 'Alicia Tan',
    phone: '+65 9123 4567',
    designerId: 101,
    propertyType: '4-Room HDB',
    areaSize: 92,
    budget: 65000,
    preferredStyle: 'Scandinavian',
    rooms: 'Living room, kitchen, master bedroom',
    expectedCompletionDate: '2027-03-30',
    additionalInfo: 'We prefer more hidden storage and easy-to-clean materials.',
    floorPlanName: 'alicia-floor-plan.pdf',
    inspirationNames: ['living-room-ref.jpg', 'kitchen-ref.jpg'],
    status: 'pending',
    createdAt: '2026-11-01',
  },
];

export const initialConsultations = [
  { id: 601, customerName: 'Alicia Tan', designerId: 101, date: '2026-11-08', time: '14:00', mode: 'In-person', status: 'confirmed' },
  { id: 602, customerName: 'Marcus Lim', designerId: 102, date: '2026-11-11', time: '19:00', mode: 'Video Call', status: 'pending' },
];

export const initialPayments = [
  { id: 701, customerName: 'Alicia Tan', designerId: 101, projectName: 'Scandinavian 4-Room HDB', amount: 5000, type: 'Deposit', status: 'Paid', date: '2026-10-15', invoiceNo: 'INV-2026-0107' },
  { id: 702, customerName: 'Alicia Tan', designerId: 101, projectName: 'Scandinavian 4-Room HDB', amount: 12000, type: 'Carpentry Milestone', status: 'Outstanding', date: '2026-11-20', invoiceNo: 'INV-2026-0121' },
];

export const initialActiveProjects = [
  {
    id: 801,
    designerId: 101,
    customerName: 'Alicia Tan',
    projectName: 'Scandinavian 4-Room HDB',
    status: 'In Progress',
    milestones: [
      { id: 1, name: 'Design Confirmation', completed: true },
      { id: 2, name: 'Demolition', completed: true },
      { id: 3, name: 'Carpentry Installation', completed: false },
      { id: 4, name: 'Final Handover', completed: false },
    ],
  },
];

export const initialCompanyReports = [
  { id: 901, designerId: 103, customerName: 'Demo Customer', reason: 'Misleading advertisement', details: 'The advertised package price did not match the quotation provided.', status: 'open', date: '2026-10-28' },
];

export const initialCategories = ['Living Room', 'Kitchen', 'Bedroom', 'Whole Home', 'Office', 'Bathroom'];
