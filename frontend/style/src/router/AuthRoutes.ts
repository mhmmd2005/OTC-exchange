const AuthRoutes = {
  path: '/auth',
  component: () => import('@/layouts/blank/BlankLayout.vue'),
  meta: {
    requiresAuth: false,
  },
  children: [
    {
      name: 'Landing Page',
      path: '/',
      component: () => import('@/views/accounts/landingpage/index.vue'),
    },
    {
      name: 'FrontPage',
      path: '/front-page/homepage',
      component: () => import('@/views/accounts/front-pages/Landingpage.vue'),
    },
    {
      name: 'About Us',
      path: '/front-page/about-us',
      component: () => import('@/views/accounts/front-pages/Aboutpage.vue'),
    },
    {
      name: 'Contact',
      path: '/front-page/contact-us',
      component: () => import('@/views/accounts/front-pages/Contactpage.vue'),
    },
    {
      name: 'Pricing1',
      path: '/front-page/pricing',
      component: () => import('@/views/accounts/front-pages/PackagePricing.vue'),
    },
    {
      name: 'Portfolio',
      path: '/front-page/portfolio',
      component: () => import('@/views/accounts/front-pages/Portfolio.vue'),
    },
    {
      name: 'Blog',
      path: '/front-page/blog/posts',
      component: () => import('@/views/accounts/front-pages/BlogPage.vue'),
    },
    {
      name: 'Blog Details',
      path: '/front-page/blog/:id',
      component: () => import('@/views/accounts/front-pages/BlogDetails.vue'),
    },
    {
      name: 'Side Login',
      path: '/login',
      component: () => import('@/views/authentication/SideLogin.vue'),
    },
    {
      name: 'Side Register',
      path: '/register',
      component: () => import('@/views/authentication/SideRegister.vue'),
    },
    {
      name: 'Side Forgot Password',
      path: '/forgot-password',
      component: () => import('@/views/authentication/SideForgotPassword.vue'),
    },
{
  path: '/reset-password-confirm/:token',
  alias: ['/reset-password-confirm/:token/'],
  name: 'ResetPasswordConfirm',
  component: () => import('@/views/authentication/ResetConfirm.vue'),
},
{
  name: 'Side Two Steps',
  path: '/two-step',
  component: () => import('@/views/authentication/SideTwoStep.vue'),
  meta: { requiresTwoFATicket: true, requiresAuth: false },
}
,
    {
      path: '/verify-email/:token',
      alias: ['/verify-email/:token/'],
      name: 'VerifyEmail',
      component: () => import('@/views/authentication/VerifyEmail.vue'),
    }
    ,
    {
      name: 'Error',
      path: '/auth/404',
      component: () => import('@/views/authentication/Error.vue'),
    },
    {
      name: 'Maintenance',
      path: '/auth/maintenance',
      component: () => import('@/views/authentication/Maintenance.vue'),
    },
  ],
};

export default AuthRoutes;
