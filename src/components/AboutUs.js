import React from 'react';

const Section = ({ title, children }) => (
  <section className="mb-12">
    <h2 className="h2 border-b-1 border-border-subtle pb-4 mb-6">
      {title}
    </h2>
    <div className="font-sans text-text-secondary leading-relaxed space-y-5 max-w-[75ch]">
      {children}
    </div>
  </section>
);

const AboutUs = () => {
  return (
    <div className="bg-background-primary min-h-full animate-fade-in">
      <div className="container mx-auto px-6 py-12 md:py-16">
        <div className="max-w-4xl mx-auto">
          <header className="text-left mb-16">
            <h1 className="h1 mb-4">
              About AusLex
            </h1>
            <p className="text-lg text-text-secondary leading-normal max-w-[75ch]">
              An exploration into fine-tuning Large Language Models for specialized legal applications within the Australian legal system.
            </p>
          </header>

          <article>
            <Section title="Introduction">
              <p>The development of domain-specific Large Language Models (LLMs) has emerged as a critical research direction in natural language processing, with particular significance in highly specialized fields such as law. Legal language processing presents unique challenges due to the domain's complex terminology, jurisdiction-specific regulations, and the critical importance of accuracy in legal interpretation.</p>
              <p>While recent advances in legal AI have demonstrated the potential of LLMs in legal tasks, most existing work focuses on US-centric legal corpora, leaving significant gaps in other legal systems, particularly Australian law. This project addresses this lacuna by presenting the first comprehensive fine-tuning of a large-scale language model specifically on Australian legal texts.</p>
            </Section>

            <Section title="Theoretical Framework">
              <p>Recent research demonstrates that domain-specific pretraining and fine-tuning significantly outperform general-purpose models on specialized tasks. This approach is particularly effective in knowledge-intensive domains like law, where it helps mitigate "legal hallucinations" and improves the accuracy of legal interpretations.</p>
              <p>Our implementation utilizes Low-Rank Adaptation (LoRA), a parameter-efficient fine-tuning technique that has shown remarkable effectiveness in domain adaptation. This method introduces low-rank matrices into the model architecture, capturing domain-specific knowledge while preserving the general capabilities of the foundation model with minimal computational cost.</p>
            </Section>
            
            <Section title="Methodology">
              <p>The Open Australian Legal Corpus is a methodologically advanced dataset incorporating documents from federal and state-level sources. We address the challenge of long legal documents through token-based chunking with overlapping windows, a technique superior to simple truncation for preserving contextual information.</p>
              <p>We implement a chat-based fine-tuning approach that incorporates document metadata (jurisdiction, document type, date) into user prompts. This creates more diverse and realistic interaction patterns that better reflect real-world legal AI applications and improve context-aware legal reasoning.</p>
            </Section>

            <footer className="mt-16 text-left text-text-placeholder border-t-1 border-border-subtle pt-8">
              <p className="text-sm">&copy; {new Date().getFullYear()} AusLex. All Rights Reserved.</p>
              <p className="text-xs mt-2">This information is for demonstration purposes only and does not constitute legal advice.</p>
            </footer>
          </article>
        </div>
      </div>
    </div>
  );
};

export default AboutUs;
