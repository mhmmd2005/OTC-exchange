<script setup lang="ts">
import { ref } from 'vue';
import { UserCircleIcon, BellIcon, ArticleIcon, LockIcon, AdjustmentsHorizontalIcon, ActivityHeartbeatIcon } from 'vue-tabler-icons';
import ProfileTab from '@/components/accounts/account-settings/ProfileTab.vue';
import SecurityTab from '@/components/accounts/account-settings/SecurityTab.vue';
import PreferencesTab from '@/components/accounts/account-settings/PreferencesTab.vue';
import ActivityLogsTab from '@/components/accounts/account-settings/ActivityLogsTab.vue';

const tab = ref<'Profile'|'Security'|'Preferences'|'Activity'|'Notification'|'Bills'>('Profile');

const page = ref({ title: 'Account Settings' });
const breadcrumbs = ref([
  { text: 'Home', disabled: false, href: '#' },
  { text: 'Account Settings', disabled: true, href: '#' }
]);
</script>

<template>
  <BaseBreadcrumb :title="page.title" :breadcrumbs="breadcrumbs" />
  <v-row class="justify-center">
    <v-col cols="12">
      <v-card elevation="10">
        <v-tabs v-model="tab" bg-color="transparent" min-height="70" height="70" color="primary">
          <v-tab value="Profile"><UserCircleIcon class="mr-2" size="20" />Profile</v-tab>
          <v-tab value="Security"><LockIcon class="mr-2" size="20" />Security</v-tab>
          <v-tab value="Preferences"><AdjustmentsHorizontalIcon class="mr-2" size="20" />Preferences</v-tab>
            <v-tab value="Activity"><AdjustmentsHorizontalIcon class="mr-2" size="20" />Activity</v-tab>

        </v-tabs>

        <v-divider />

        <v-card-text class="pa-sm-6 pa-3 pb-sm-6 pb-6">
          <v-window v-model="tab">
            <v-window-item value="Profile">
              <ProfileTab />
            </v-window-item>
            <v-window-item value="Security">
              <SecurityTab />
            </v-window-item>
            <v-window-item value="Preferences">
              <PreferencesTab />
            </v-window-item>
            <v-window-item value="Activity">
              <ActivityLogsTab />
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
