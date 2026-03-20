<script setup>
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'

const router = useRouter()

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <div class="max-w-3xl mx-auto px-4 py-12">
      <Button variant="ghost" class="mb-6" @click="goBack">
        &larr; Back
      </Button>

      <h1 class="text-4xl font-bold mb-2">Privacy Policy</h1>
      <p class="text-muted-foreground mb-8">Last updated: March 15, 2026</p>

      <div class="prose prose-sm max-w-none space-y-8 text-foreground/90">
        <section>
          <h2 class="text-2xl font-semibold mb-3">1. Data Collection</h2>
          <p>
            We collect information you provide directly to us when you create an account, including your
            name, email address, and password. We also collect data about your reading activity, including
            books added, reading progress, reviews, notes, and quotes.
          </p>
          <p>
            We automatically collect certain technical information when you use the Service, such as your
            IP address, browser type, and device information. This data helps us improve the Service and
            ensure its security.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">2. Data Usage</h2>
          <p>
            We use your information to provide, maintain, and improve the Service. This includes personalizing
            your experience, generating reading recommendations, and enabling social features such as friend
            connections and reading circles.
          </p>
          <p>
            We do not sell your personal information to third parties. We may use aggregated, anonymized data
            for analytics and service improvement purposes.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">3. Data Storage</h2>
          <p>
            Your data is stored securely using industry-standard encryption and security practices. We retain
            your data for as long as your account is active or as needed to provide the Service.
          </p>
          <p>
            Backups of your data are maintained to prevent data loss. You may request a full export of your
            data at any time through the Settings page.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">4. User Rights</h2>
          <p>
            You have the right to access, correct, or delete your personal information at any time. You can
            update your profile information through the Settings page or request account deletion by
            contacting us.
          </p>
          <p>
            You have the right to export all your data in a portable format. You may also request that we
            restrict or cease processing your personal information.
          </p>
          <p>
            If you are located in the European Economic Area, you have additional rights under the General
            Data Protection Regulation (GDPR), including the right to data portability and the right to
            lodge a complaint with a supervisory authority.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">5. Contact</h2>
          <p>
            If you have any questions about this Privacy Policy or our data practices, please contact us
            at privacy@marginalia.app.
          </p>
          <p>
            For data-related requests such as account deletion or data export, please use the Settings page
            within the application or email us directly.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>
