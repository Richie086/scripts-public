## **The Accidental Tech Writer: How a Massive Outage Changed My Career**

I have a confession to make: I have a background in Technical Writing, but I never received a single day of formal training in the subject.

I fell into the profession completely by accident early in my career while working as a Tier 2 Technical Support agent. If you've ever worked in IT support, you know the drill—I was answering phones and tackling the escalated issues the front line group couldn't handle. If a problem required more than a simple password reset, it came directly to my team.

At the time, I was working as a contractor for Pacific Gas and Electric (PG&E).

PG&E's tech stack was nothing short of impressive. They relied on millions of sensors scattered across California, continuously measuring the flow of energy from Point A to Point B.

This environment was my introduction to massive, complex technologies like Global Information Systems (GIS)—a framework that captures, manages, analyzes, and maps spatial and geographical data. PG&E truly had a little bit of everything, including legacy systems at nuclear plants that had been running non-stop for 30 years.

A company of that scale naturally relied heavily on SAP for its daily operations. One day, a routine update was rolled out—and it immediately broke authentication across the board. Suddenly, an entire massive utility company was completely dead in the water, unable to work.

This was back in the era when Windows XP and Windows 2000 were the primary operating systems dominating the enterprise workspace.

As the calls flooded in, I started digging into the problem and discovered a reliable fix for the authentication loop. However, there was a catch: the resolution procedure depended entirely on which OS the user had. Each system required its own distinct set of troubleshooting steps.

# **From Troubleshooting to Technical Writing**

Realizing we had thousands of panicked users sitting in the call queue, I knew we didn't have time to figure it out case-by-case. I quickly documented both procedures, wrote up clear, step-by-step instructions for Windows XP and Windows 2000, and blasted the email out to everyone on my Tier 2 team.

Armed with the new documentation, my team was able to rapidly resolve the issue for each user and burn through the backlog. Before long, the massive call queue was entirely empty.

I received a lot of gratitude from the team for sending out those instructions, but the real turning point happened shortly after. My supervisor walked over to my desk and asked a question that shifted my entire career trajectory:

"Have you ever thought about being a technical writer?"

According to him, if I was interested in the position, two things would happen immediately: I would never have to take another tech support call, and I would be getting a significant bump in pay.

I didn't have the training, but I had the job. And that is exactly how my career in Technical Writing began.

## **Leveling Up at Intel: Documenting the Integrated Graphics Revolution**

My next big technical writing gig brought me to Intel in Folsom, California. I joined a dedicated team of technical writers tasked with creating something incredibly important: a behavior specification.

At the time, Intel was rolling out something genuinely groundbreaking—a CPU with integrated graphics built right onto the die. Our behavior spec was the ultimate guide, designed to teach developers exactly how to write software that could take full advantage of these new hardware capabilities.

## **Discovering the Magic of MadCap Flare**

This project was also my first introduction to the world of MadCap Flare.

If you aren't familiar with it, MadCap Flare is what the industry calls a single-sourcing tool. It completely changed how I looked at documentation. Instead of writing separate manuals from scratch for every single processor variation, we could write our content in a modular, highly efficient way.

We documented how the architecture worked across every evolution of the CPU, covering all the intricate registers, logic, and technical details required to write compatible software. From that single source of truth, MadCap Flare allowed us to automatically generate documentation tailored to a specific CPU model.

With a few clicks, we could produce all sorts of dynamic outputs, including:

- HTML 5
- Adobe PDF
- MS Word

## **Blurring the Lines: From Writer to System Administrator**

Because the specifications were constantly evolving, changes were being made to the documentation on a daily basis. Those updates needed to be compiled into brand-new outputs and made immediately accessible to stakeholders internally via HTTPS and CIFS file shares.

Prior to my joining the team, these documents were not being generated on an ongoing, automated basis. My role quickly evolved from strictly technical writing into a hybrid of technical writing and system administration—a shift I felt very comfortable making.

I took on the responsibility of ensuring a reliable, updated behavior spec was produced in several formats, multiple times a day. These outputs were heavily relied upon by groups both inside and outside of Intel. It was my first real taste of seeing my documentation scale so widely; because it touched so many coworkers, it had to be relevant, continuously updated, and always accessible.

Since none of this automated capability existed within my original team, I built the entire infrastructure from start to finish.

You have to remember, this was back before modern system orchestration technologies like PowerShell even existed. This meant the entire pipeline was built on good ol' Windows Batch files. I wrote automated scripts that would kick off, compile, and produce the newly updated outputs—generating one spec for the Ivy Bridge CPU registers, and simultaneously kicking off another for the Sandy Bridge CPU architecture.

To support this rapid generation, I implemented several redundant Windows server and desktop solutions. This gave my team of technical writers dedicated, physical systems they could reliably use to make continuous changes to the documentation without worrying about downtime.

By this point, our documentation repository had grown into a massive 200GB collection of CPU registers, architecture logic, and all the other intricate odds and ends developers needed to know to write compatible software.

Now, I want to be clear: I am not a software developer. I don't pretend to fully understand all the specific hurdles they faced writing code back in an era long before ubiquitous on-premise virtualization and cloud computing became the norm.

But from an infrastructure and technical writing standpoint? I can confidently say that what we were doing was incredibly advanced. The fully automated, highly redundant documentation engine my group was producing on a continuous, rolling basis far exceeded the standard documentation capabilities of the time.
