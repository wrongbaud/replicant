# Replicant

Fault Injection Research and Resources - read corresponding blog post [here](https://voidstarsec.com/blog/replicant-part-1)

# Contents

- ```replicant.py``` - Glitching code for ChipWhisperer
- ```usbreset.c``` - C Code for USB device reset (for STLink)

# Dependencies

- [pyswd](https://github.com/cortexm/pyswd)
- [pyocd](https://github.com/pyocd/pyOCD) 

# Working offsets 
- 19743 
- 19757 
- 19761
- 19780
- 19752
- 19531
- 19629
- 19618
- 19620

# Reference Materials

- [Read secure firmware using CW](https://prog.world/read-secure-firmware-from-stm32f1xx-flash-using-chipwhisperer/)
- [Kraken Article](https://blog.kraken.com/post/3662/kraken-identifies-critical-flaw-in-trezor-hardware-wallets/)
- [chip.fail](https://chip.fail/chipfail.pdf)
    - [Ref 1 ](https://www.usenix.org/system/files/conference/woot17/woot17-paper-obermaier.pdf)
    - [Ref 2 ](https://tches.iacr.org/index.php/TCHES/article/download/7390/6562/)
    - [Ref 3 ](http://circuitcellar.com/cc-blog/verifying-code-readout-protection-claims/)
- [Shunt Resistor / Power Analysis Article](https://research.kudelskisecurity.com/2019/10/16/power-analysis-to-the-people/)
- [STM32 Datasheet](https://www.st.com/resource/en/datasheet/cd00237391.pdf)
- [Grands Slides](http://www.grandideastudio.com/wp-content/uploads/wallet_hack_slides.pdf)
- [CW Hardware Information](https://rtfm.newae.com/Capture/ChipWhisperer-Lite/)
