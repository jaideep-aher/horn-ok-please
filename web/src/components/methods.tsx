import type { Summary } from "@/lib/types";

const CITATIONS = [
  {
    href: "https://arxiv.org/abs/2405.14169",
    text: "Chung, Gao, Vu, Zhang, Liu, Lin, Dong, and Guo. Towards Transferable Attacks Against Vision-LLMs in Autonomous Driving with Typography. arXiv:2405.14169, 2024.",
  },
  {
    href: "https://arxiv.org/abs/2510.00181",
    text: "Burbano, Ortiz, Sun, Yang, Tu, Xie, Cao, and Cardenas. CHAI: Command Hijacking against embodied AI. arXiv:2510.00181. The abstract reports attack success up to 95.5% on CloudTrack, 81.8% on DriveLM, and 72.8% on drone landing in simulation, and at least 87% in real-world robotic vehicle experiments.",
  },
  {
    href: "https://arxiv.org/abs/2504.04893",
    text: "Westerhoff, Purelku, Hackstein, Loos, Pinetzki, Rodner, and Hufe. SCAM. arXiv:2504.04893, 2025. The abstract describes 1,162 real-world typographic images.",
  },
  {
    href: "https://arxiv.org/abs/2503.04982",
    text: "Kundu, Bhiwandiwalla, Yu, Howard, Le, Sridhar, Kang, Cobbley, and Lal. LVLM-Compress-Bench. arXiv:2503.04982, 2025. Compression of vision-language models, not a driving-script study.",
  },
  {
    href: "https://arxiv.org/abs/2511.23071",
    text: "De and colleagues. Bharat Scene Text. arXiv:2511.23071. More than 100K words, 11 Indian languages and English, 6,582 images. Not used in this run.",
  },
  {
    href: "https://arxiv.org/abs/2510.21689",
    text: "Zhou, Aghakishiyeva, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. On Thin Ice. arXiv:2510.21689. NeurIPS Imageomics Workshop 2025, from the arXiv comment. Adapted here as a scoring template (localization, deletion or insertion, failure labels), not as a seal-detector result.",
  },
  {
    href: "https://arxiv.org/abs/2510.03317",
    text: "Aghakishiyeva, Zhou, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. Photorealistic Inpainting for Perturbation-based Explanations in Ecological Monitoring. arXiv:2510.03317. NeurIPS 2025 Imageomics Workshop, from the arXiv comment. Adapted as mask-local removal. This run does not use their Segment Anything or Stable Diffusion pipeline.",
  },
  {
    href: "https://arxiv.org/abs/2608.20670",
    text: "Mendi and Bent. Why2Speak: Faithful Reasoning for Abstaining Action Policies. arXiv:2608.20670. Adapted as a direct decision versus a reason-then-decide prompt. Their probes and conversation task are not run.",
  },
  {
    href: "https://arxiv.org/abs/2604.09923",
    text: "Ding, Bent, and Wendell. GLEaN: A Text-to-image Bias Detection Approach for Public Comprehension. arXiv:2604.09923. CVPR Workshops 2026, pp. 4026–4036. Cited for the public-facing aim. Their portrait study is not run. The expo form on this page does not collect responses.",
  },
  {
    href: "https://arxiv.org/abs/2602.12877",
    text: "Iyer, Rathinagiriswaran, and Jyothikamalesh. RoadscapesQA. arXiv:2602.12877. Up to 9,000 Indian road images. Not used in this run.",
  },
];

export function Methods({ summary }: { summary: Summary | null }) {
  return (
    <section id="methods" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Methods</p>
      <h2 className="mt-2 font-display text-4xl">Locked before the first scored reply</h2>
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <article className="space-y-3 text-sm leading-relaxed">
          <p>
            The first contract is <code>eval/preregistration.md</code>. Round 2 is{" "}
            <code>eval/round2/preregistration.md</code>. Round 3, <code>eval/round3/preregistration.md</code>,
            changes the decision to STOP or GO, because a still frame cannot support the four-way split. The
            prompt diagnostic is <code>eval/dev/protocol.md</code>, locked on new drawings before those
            completions. The explanation protocol is <code>eval/xai/protocol.md</code>. It does not rescore the
            locked scenes. A round-4 file exists only if a wording cleared that dev gate, and only if it was
            dated before any new completion on the locked scenes. Intervals are 95% Wilson. Paired tests are
            exact McNemar, Holm-adjusted inside the declared family.
          </p>
          <p>
            Round 1 used SmolVLM. Round 2 added Qwen2.5-VL 3B, Gemma 3 4B, and InternVL2.5 1B under llama.cpp,
            greedy, with a grammar. Round 3 kept Qwen and Gemma at Q8_0 and Q4_K_M and did not enroll
            InternVL. The dev diagnostic used the two Q8 models. The Gemini client lists models at runtime
            when a key is set, and GEMINI_MODEL overrides that list. On 18 October 2026 the bundle in
            eval/gemini_remote resolved gemini-3.8-flash and ran the same locked gate, attacks, defenses,
            explanation scenes, and photographs. Its rows and summaries are in eval/gemini_remote/results.
          </p>
          <p>
            Scenes are synthetic 1280×720 illustrations drawn for this study, licensed CC-BY-4.0 by
            Jaideep (Jay) Aher. They are not dashcam frames, not the Indian Driving Dataset, and not
            RoadscapesQA or Bharat Scene Text. Those sets are cited because they are the right next
            corpora, and they were not downloaded.
          </p>
          <p>
            {summary?.n_records
              ? `The summary currently holds ${summary.n_records} records, ${summary.n_drive_records ?? "—"} of them driving trials.`
              : "Record counts appear here when the summary file is ready."}
          </p>
        </article>
        <article>
          <h3 className="font-display text-2xl">Still pending</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
            <li>
              GPT-4o and Claude on the same locked scenes. Only Gemini has been called so far.
            </li>
            <li>Photograph transfer on the open-weight models. The photograph run so far is Gemini only.</li>
            <li>Scoring road-surface placement, other plate sizes, and more than one phrase per script.</li>
            <li>Quantizing the vision projector, not only the language weights.</li>
            <li>A correlation of literacy with attack success, which needs more than four models.</li>
            <li>Physical transfer. Out of scope, and not a future task this repo will instruct.</li>
          </ul>
        </article>
      </div>
      <h3 className="mt-10 font-display text-2xl">Anchors</h3>
      <ul className="mt-3 space-y-3 text-sm leading-relaxed">
        {CITATIONS.map((item) => (
          <li key={item.href}>
            <a className="underline decoration-yellow decoration-2 underline-offset-2" href={item.href}>
              {item.text}
            </a>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-muted">
        Abstracts were checked on 18 October 2026. CHAI’s percentages are the abstract’s, not this
        study’s. This page does not repeat an attack-success figure from Chung et al., because that
        figure was not extracted from the paper.
      </p>
    </section>
  );
}
