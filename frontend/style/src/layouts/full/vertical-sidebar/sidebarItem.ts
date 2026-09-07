export interface menu {
    header?: string;
    title?: string;
    icon?: any;
    to?: string;
    chip?: string;
    BgColor?: string;
    chipBgColor?: string;
    chipColor?: string;
    chipVariant?: string;
    chipIcon?: string;
    children?: menu[];
    disabled?: boolean;
    type?: string;
    subCaption?: string;
}

const sidebarItem: menu[] = [
    { header: 'Home' },
    {
        title: 'Dashboard',
        icon: 'screencast-2-linear',
        BgColor: 'primary',
        to: '/dashboard1'
    },
    {
        title: 'Dashboard 2',
        icon: 'chart-line-duotone',
        BgColor: 'success',
        to: '/dashboard2'
    },
    {
        title: 'Front Pages',
        icon: 'home-angle-linear',
        BgColor: 'warning',
        to: '/',
        children: [
            {
                title: 'Homepage',
                to: '/front-page/homepage'
            },
            {
                title: 'About Us',
                to: '/front-page/about-us'
            },
            {
                title: 'Blog',
                to: '/front-page/blog/posts'
            },
            {
                title: 'Blog Details',
                to: '/front-page/blog/early-black-friday-amazon-deals-cheap-tvs-headphones'
            },
            {
                title: 'Contact Us',
                to: '/front-page/contact-us'
            },
            {
                title: 'Portfolio',
                to: '/front-page/portfolio'
            },
            {
                title: 'Pricing',
                to: '/front-page/pricing'
            }
        ]
    },

    { header: 'Apps' },
    {
        title: 'Contact',
        icon: 'phone-line-duotone',
        BgColor: 'secondary',
        to: '/apps/contacts'
    },

    {
        title: 'Blog',
        icon: 'align-vertical-spacing-line-duotone',
        BgColor: 'warning',
        to: '/',
        children: [
            {
                title: 'Posts',
                to: '/apps/blog/posts'
            },
            {
                title: 'Detail',
                to: '/apps/blog/early-black-friday-amazon-deals-cheap-tvs-headphones'
            }
        ]
    },
    {
        title: 'E-Commerce',
        icon: 'smart-speaker-minimalistic-line-duotone',
        to: '/ecommerce/',
        BgColor: 'indigo',
        children: [
            {
                title: 'Shop One',
                to: '/ecommerce/products-one'
            },
            {
                title: 'Shop Two',
                to: '/ecommerce/products-two'
            },
            {
                title: 'Details One',
                to: '/ecommerce/product/detail/one/1'
            },
            {
                title: 'Details Two',
                to: '/ecommerce/product/detail/two/1'
            },
            {
                title: 'List',
                to: '/ecommerce/productlist'
            },
            {
                title: 'Checkout',
                to: '/ecommerce/checkout'
            },
            {
                title: 'Add Product',
                to: '/ecommerce/add-product'
            },
            {
                title: 'Edit Product',
                to: '/ecommerce/edit-product'
            }
        ]
    },
    {
        title: 'Chats',
        icon: 'chat-round-unread-line-duotone',
        BgColor: 'primary',
        to: '/apps/chats'
    },
    {
        title: 'User Profile',
        icon: 'user-rounded-line-duotone',
        BgColor: 'error',
        to: '/',
        children: [
            {
                title: 'Profile One',
                to: '/apps/user/profileone'
            },
            {
                title: 'Profile Two',
                to: '/apps/user/profiletwo'
            }
        ]
    },
    {
        title: 'Invoice',
        icon: 'bill-check-outline',
        BgColor: 'success',
        to: '/',
        children: [
            {
                title: 'List',
                to: '/apps/invoice'
            },
            {
                title: 'Details',
                to: '/apps/invoice/details/102'
            },
            {
                title: 'Create',
                to: '/apps/invoice/create'
            },
            {
                title: 'Edit',
                to: '/apps/invoice/edit/102'
            }
        ]
    },
    {
        title: 'Notes',
        icon: 'notification-unread-line-duotone',
        BgColor: 'secondary',
        to: '/apps/notes'
    },
    {
        title: 'Calendar',
        icon: 'calendar-line-duotone',
        BgColor: 'info',
        to: '/apps/calendar'
    },
    {
        title: 'Email',
        BgColor: 'error',
        icon: 'letter-linear',
        to: '/apps/email'
    },
    {
        title: 'Kanban',
        icon: 'widget-4-linear',
        BgColor: 'warning',
        to: '/apps/kanban'
    },
    {
        title: 'Tickets',
        icon: 'ticker-star-outline',
        BgColor: 'primary',
        to: '/apps/tickets'
    },
    { header: 'Pages' },
    {
        title: 'Pricing',
        icon: 'tag-price-line-duotone',
        BgColor: 'warning',
        to: '/pages/pricing'
    },
    {
        title: 'FAQ',
        icon: 'question-circle-line-duotone',
        BgColor: 'error',
        to: '/pages/faq'
    },
    {
        title: 'Account Setting',
        icon: 'settings-minimalistic-line-duotone',
        BgColor: 'success',
        to: '/pages/account-settings'
    },
    {
        title: 'Landing Page',
        icon: 'layers-minimalistic-line-duotone',
        BgColor: 'info',
        to: '/'
    },
    {
        title: 'Gallery Lightbox',
        icon: 'gallery-minimalistic-outline',
        BgColor: 'warning',
        to: '/pages/gallery-lightbox'
    },
    {
        title: 'Search Results',
        icon: 'calendar-search-line-duotone',
        BgColor: 'success',
        to: '/pages/search-results'
    },
    {
        title: 'Social Contacts',
        icon: 'socket-outline',
        BgColor: 'primary',
        to: '/pages/social-media-contacts'
    },
    {
        title: 'Treeview',
        icon: 'transmission-line-duotone',
        BgColor: 'error',
        to: '/pages/treeview'
    },

    {
        title: 'Widget',
        icon: 'widget-add-line-duotone',
        to: '/widget-card',
        BgColor: 'primary',
        children: [
            {
                title: 'Cards',
                to: '/widgets/cards'
            },
            {
                title: 'Banners',
                to: '/widgets/banners'
            },
            {
                title: 'Charts',
                to: '/widgets/charts'
            }
        ]
    },

    { header: 'School Pages' },
    {
        title: 'Teachers',
        icon: 'square-academic-cap-linear',
        to: '',
        BgColor: 'success',
        children: [
            {
                title: 'All Teachers',
                to: '/teachers/all-teachers'
            },
            {
                title: 'Teachers Details',
                to: '/teachers/teachers-details'
            }
        ]
    },
    {
        title: 'Exam',
        icon: 'notebook-minimalistic-outline',
        to: '',
        BgColor: 'warning',
        children: [
            {
                title: 'Exam Schedule',
                to: '/exam/exam-schedule'
            },
            {
                title: 'Exam Result',
                to: '/exam/exam-result'
            },
            {
                title: 'Exam Result Details',
                to: '/exam/exam-result-details'
            }
        ]
    },
    {
        title: 'Students',
        icon: 'case-broken',
        to: '',
        BgColor: 'error',
        children: [
            {
                title: 'All Students',
                to: '/students/all-students'
            },
            {
                title: 'Students Details',
                to: '/students/students-details'
            }
        ]
    },
    {
        title: 'Classes',
        icon: 'smart-home-broken',
        BgColor: 'indigo',
        to: '/school-pages/classes'
    },
    {
        title: 'Attendance',
        icon: 'diploma-linear',
        BgColor: 'info',
        to: '/school-pages/attendance'
    },
    { header: 'UI' },
    {
        title: 'Ui Elements',
        icon: 'code-scan-line-duotone',
        BgColor: 'primary',
        to: '/components/',
        children: [
            {
                title: 'Alert',
                to: '/ui-components/alert'
            },
            {
                title: 'Accordion',
                to: '/ui-components/accordion'
            },
            {
                title: 'Avatar',
                to: '/ui-components/avatar'
            },
            {
                title: 'Chip',
                to: '/ui-components/chip'
            },
            {
                title: 'Dialog',
                to: '/ui-components/dialogs'
            },
            {
                title: 'List',
                to: '/ui-components/list'
            },
            {
                title: 'Menus',
                to: '/ui-components/menus'
            },
            {
                title: 'Rating',
                to: '/ui-components/rating'
            },
            {
                title: 'Tabs',
                to: '/ui-components/tabs'
            },
            {
                title: 'Tooltip',
                to: '/ui-components/tooltip'
            },
            {
                title: 'Typography',
                to: '/ui-components/typography'
            }
        ]
    },

    { header: 'Forms' },
    {
        title: 'Form Elements',
        icon: 'widget-3-line-duotone',
        BgColor: 'secondary',
        to: '/components/',
        children: [
            {
                title: 'Autocomplete',
                to: '/forms/form-elements/autocomplete'
            },
            {
                title: 'Combobox',
                to: '/forms/form-elements/combobox'
            },
            {
                title: 'Button',
                to: '/forms/form-elements/button'
            },
            {
                title: 'Checkbox',
                to: '/forms/form-elements/checkbox'
            },
            {
                title: 'Custom Inputs',
                to: '/forms/form-elements/custominputs'
            },
            {
                title: 'File Inputs',
                to: '/forms/form-elements/fileinputs'
            },
            {
                title: 'Radio',
                to: '/forms/form-elements/radio'
            },
            {
                title: 'Date Time',
                to: '/forms/form-elements/date-time'
            },
            {
                title: 'Select',
                to: '/forms/form-elements/select'
            },
            {
                title: 'Slider',
                to: '/forms/form-elements/slider'
            },
            {
                title: 'Switch',
                to: '/forms/form-elements/switch'
            },
            {
                title: 'Time Picker',
                to: '/forms/form-elements/time-picker'
            },
            {
                title: 'Stepper',
                to: '/forms/form-elements/stepper'
            }
        ]
    },

    {
        title: 'Form Input',
        icon: 'book-minimalistic-outline',
        BgColor: 'success',
        to: '/forms/',
        children: [
            {
                title: 'Form Layout',
                to: '/forms/form-layouts'
            },
            {
                title: 'Form Horizontal',
                to: '/forms/form-horizontal'
            },
            {
                title: 'Form Vertical',
                to: '/forms/form-vertical'
            },
            {
                title: 'Form Custom',
                to: '/forms/form-custom'
            },
            {
                title: 'Form Validation',
                to: '/forms/form-validation'
            }
        ]
    },
    {
        title: 'Editor',
        icon: 'gallery-edit-line-duotone',
        BgColor: 'warning',
        to: '/forms/editor'
    },

    { header: 'Tables' },
    {
        title: 'Basic Table',
        icon: 'tablet-line-duotone',
        BgColor: 'info',
        to: '/tables/basic'
    },
    {
        title: 'Dark Table',
        icon: 'bedside-table-2-linear',
        BgColor: 'success',
        to: '/tables/dark'
    },
    {
        title: 'Density Table',
        icon: 'password-minimalistic-input-linear',
        BgColor: 'error',
        to: '/tables/density'
    },
    {
        title: 'Fixed Header Table',
        icon: 'align-left-line-duotone',
        BgColor: 'indigo',
        to: '/tables/fixed-header'
    },
    {
        title: 'Height Table',
        icon: 'bookmark-square-minimalistic-outline',
        BgColor: 'warning',
        to: '/tables/height'
    },
    {
        title: 'Editable Table',
        icon: 'pen-new-square-broken',
        BgColor: 'success',
        to: '/tables/editable'
    },

    { header: 'Data Tables' },
    {
        title: 'Basic Table',
        icon: 'database-outline',
        BgColor: 'primary',
        to: '/tables/datatables/basic'
    },
    {
        title: 'Header Table',
        icon: 'clapperboard-text-broken',
        BgColor: 'secondary',
        to: '/tables/datatables/header'
    },
    {
        title: 'Selection Table',
        icon: 'documents-minimalistic-linear',
        BgColor: 'success',
        to: '/tables/datatables/selection'
    },
    {
        title: 'Sorting Table',
        icon: 'sort-from-bottom-to-top-linear',
        BgColor: 'error',
        to: '/tables/datatables/sorting'
    },
    {
        title: 'Pagination Table',
        icon: 'programming-linear',
        BgColor: 'warning',
        to: '/tables/datatables/pagination'
    },
    {
        title: 'Filtering Table',
        icon: 'filter-outline',
        BgColor: 'indigo',
        to: '/tables/datatables/filtering'
    },
    {
        title: 'Grouping Table',
        icon: 'users-group-rounded-line-duotone',
        BgColor: 'info',
        to: '/tables/datatables/grouping'
    },
    {
        title: 'Table Slots',
        icon: 'server-line-duotone',
        BgColor: 'error',
        to: '/tables/datatables/slots'
    },
    {
        title: 'CRUD Table',
        icon: 'medal-star-square-outline',
        BgColor: 'success',
        to: '/tables/datatables/crudtable'
    },

    { header: 'Charts' },
    {
        title: 'Apex Charts',
        icon: 'pie-chart-2-linear',
        BgColor: 'primary',
        to: '/charts/',
        children: [
            {
                title: 'Line',
                to: '/charts/line-chart'
            },
            {
                title: 'Gredient',
                to: '/charts/gredient-chart'
            },
            {
                title: 'Area',
                to: '/charts/area-chart'
            },
            {
                title: 'Candlestick',
                to: '/charts/candlestick-chart'
            },
            {
                title: 'Column',
                to: '/charts/column-chart'
            },
            {
                title: 'Doughnut & Pie',
                to: '/charts/doughnut-pie-chart'
            },
            {
                title: 'Radialbar & Radar',
                to: '/charts/radialbar-chart'
            }
        ]
    },

    { header: 'Authentication' },

    {
        title: 'Login',
        icon: 'login-2-line-duotone',
        BgColor: 'warning',
        to: '#',
        children: [
            {
                title: 'Side Login',
                to: '/auth/login'
            },
            {
                title: 'Boxed Login',
                to: '/auth/login2'
            }
        ]
    },
    {
        title: 'Register',
        icon: 'user-plus-line-duotone',
        BgColor: 'error',
        to: '#',
        children: [
            {
                title: 'Side Register',
                to: '/auth/register'
            },
            {
                title: 'Boxed Register',
                to: '/auth/register2'
            }
        ]
    },
    {
        title: 'Forgot Password',
        icon: 'forbidden-line-duotone',
        BgColor: 'indigo',
        to: '#',
        children: [
            {
                title: 'Side Forgot Password',
                to: '/auth/forgot-password'
            },
            {
                title: 'Boxed Forgot Password',
                to: '/auth/forgot-password2'
            }
        ]
    },
    {
        title: 'Two Steps',
        icon: 'users-group-two-rounded-line-duotone',
        BgColor: 'info',
        to: '#',
        children: [
            {
                title: 'Side Two Steps',
                to: '/auth/two-step'
            },
            {
                title: 'Boxed Two Steps',
                to: '/auth/two-step2'
            }
        ]
    },

    {
        title: 'Error',
        icon: 'bug-line-duotone',
        BgColor: 'error',
        to: '/auth/404'
    },
    {
        title: 'Maintenance',
        icon: 'settings-line-duotone',
        BgColor: 'primary',
        to: '/auth/maintenance'
    },
    { header: 'Icons' },
    {
        title: 'Tabler Icons',
        BgColor: 'success',
        icon: 'sticker-smile-circle-2-line-duotone',
        to: '/icons/tabler'
    },
    {
        title: 'Solar Icons',
        BgColor: 'primary',
        icon: 'sticker-smile-circle-2-line-duotone',
        to: '/icons/solar'
    },

    { header: 'Others' },
    {
        title: 'Menu Level',
        icon: 'double-alt-arrow-down-bold-duotone',
        BgColor: 'secondary',
        to: '#',
        children: [
            {
                title: 'Level 1',
                to: '/auth/404'
            },
            {
                title: 'Level 1',
                to: '/auth/404',
                children: [
                    {
                        title: 'Level 2',

                        to: '/auth/404'
                    },
                    {
                        title: 'Level 2',

                        to: '/auth/404',
                        children: [
                            {
                                title: 'Level 3',

                                to: '/auth/404'
                            },
                            {
                                title: 'Level 3',

                                to: '/auth/404'
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        title: 'Disabled',
        icon: 'forbidden-circle-line-duotone',
        BgColor: 'success',
        disabled: true,
        to: '/auth/404'
    },
    {
        title: 'Sub Caption',
        BgColor: 'warning',
        icon: 'square-academic-cap-line-duotone',
        subCaption: 'This is the subtitle',
        to: '/auth/404'
    },
    {
        title: 'Chip',
        icon: 'archive-check-line-duotone',
        chip: '9',
        BgColor: 'error',
        chipColor: 'error',
        chipBgColor: 'error',
        chipVariant: 'flat',
        to: '/auth/404'
    },
    {
        title: 'Outlined',
        icon: 'smile-circle-line-duotone',
        chip: 'outline',
        chipColor: 'indigo',
        chipVariant: 'outlined',
        BgColor: 'indigo',
        to: '/auth/404'
    },
    {
        title: 'External Link',
        icon: 'link-bold-duotone',
        BgColor: 'info',
        to: '/auth/404',
        type: 'external'
    }
];

export default sidebarItem;
