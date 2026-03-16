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

      <h1 class="text-4xl font-bold mb-2">Terms of Service</h1>
      <p class="text-muted-foreground mb-8">Last updated: March 15, 2026</p>

      <div class="prose prose-sm max-w-none space-y-8 text-foreground/90">
        <section>
          <h2 class="text-2xl font-semibold mb-3">1. Terms of Use</h2>
          <p>
            By accessing and using Marginalia ("the Service"), you agree to be bound by these Terms of Service.
            If you do not agree to these terms, please do not use the Service.
          </p>
          <p>
            The Service is provided for personal, non-commercial use. You must be at least 13 years of age to
            use this Service. By using the Service, you represent and warrant that you meet this age requirement.
          </p>
          <p>
            We reserve the right to modify these terms at any time. Continued use of the Service after changes
            constitutes acceptance of the modified terms.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">2. User Content</h2>
          <p>
            You retain ownership of all content you create on the Service, including reviews, notes, quotes,
            and reading lists. By posting content, you grant us a non-exclusive, worldwide, royalty-free license
            to display and distribute your content within the Service.
          </p>
          <p>
            You are responsible for the content you post. Content must not violate any applicable laws,
            infringe on third-party rights, or contain harmful, abusive, or misleading material.
          </p>
          <p>
            We reserve the right to remove content that violates these terms without prior notice.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">3. Privacy</h2>
          <p>
            Your privacy is important to us. Please review our
            <router-link to="/privacy" class="text-primary hover:underline">Privacy Policy</router-link>
            to understand how we collect, use, and protect your personal information.
          </p>
          <p>
            By using the Service, you consent to the collection and use of information as described in our
            Privacy Policy.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">4. Intellectual Property</h2>
          <p>
            The Service and its original content (excluding user-generated content), features, and functionality
            are owned by Marginalia and are protected by international copyright, trademark, and other
            intellectual property laws.
          </p>
          <p>
            Book metadata, cover images, and related bibliographic information may be sourced from third-party
            providers and remain the property of their respective owners.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold mb-3">5. Limitation of Liability</h2>
          <p>
            The Service is provided on an "as is" and "as available" basis without warranties of any kind,
            either express or implied.
          </p>
          <p>
            In no event shall Marginalia, its directors, employees, or agents be liable for any indirect,
            incidental, special, consequential, or punitive damages arising out of or related to your use
            of the Service.
          </p>
          <p>
            We do not guarantee that the Service will be uninterrupted, secure, or error-free. We are not
            responsible for any loss of data or content.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>
