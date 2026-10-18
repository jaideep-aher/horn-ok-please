export function Misuse() {
  return (
    <section id="misuse" className="border-t border-line bg-ink text-paper">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <p className="font-stencil text-sm tracking-[0.16em] text-yellow uppercase">Misuse and limits</p>
        <h2 className="mt-2 font-display text-4xl">Who this is for, and what it is not</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-2">
          <div>
            <h3 className="font-display text-2xl text-yellow">Stakeholders</h3>
            <ul className="mt-3 space-y-3 text-sm leading-relaxed text-paper/85">
              <li>People in the lane who never agreed to be a caption: a person on a crossing, a child at the curb, a cow.</li>
              <li>Truck drivers, for whom tailgate paint is ordinary culture and, in a picture, a surface someone can imitate.</li>
              <li>Teams putting small vision-language models into a dashboard or an assist prototype, including teams that quantize to fit a device.</li>
              <li>Regulators and insurers who might treat a demo as a safety case. This study is not one.</li>
              <li>Readers and non-readers of Devanagari. The model’s reading is measured on cards, not assumed from the script.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-display text-2xl text-yellow">Do not take this onto a road</h3>
            <ul className="mt-3 space-y-3 text-sm leading-relaxed text-paper/85">
              <li>Do not paint these phrases on a vehicle, a wall, or a road. The generator builds labeled audit images. It is not a physical recipe, and this project did not test a moving vehicle.</li>
              <li>The defense ships in the same package as the generator. An audit kit that only offers the attack is the wrong artifact.</li>
              <li>A flip on an illustration is evidence about the proxy. It is not a measured probability of a crash.</li>
              <li>API models, photograph transfer, and a larger phrase set are pending. Their absence is a gap, not a quiet zero.</li>
            </ul>
          </div>
        </div>
        <div className="mt-8 rounded-lg border border-yellow/40 p-5 text-sm leading-relaxed">
          <h3 className="font-display text-2xl text-yellow">Limits that stay even after the numbers land</h3>
          <p className="mt-2 text-paper/85">
            Twelve original illustrations, ten of them in the primary rate, one phrase per script, one
            plate size, tailgate only. Four SmolVLM checkpoints on CPU. The edge file is Q4_0 at 5.20
            bits per weight as reported by llama-quantize, with the vision projector left at f16. Tesseract
            is a weak reader of a STOP octagon. The parser is strict, so a chatty answer becomes
            unparseable rather than a flip. No human driver was asked to label the same frames.
          </p>
        </div>
      </div>
    </section>
  );
}
