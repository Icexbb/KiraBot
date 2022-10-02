const imgs = document.getElementsByTagName("img");
    //const xposi = [30, 380, 730, 1080, 1430, 1780, 2130];
    //const yposi = [20, 360, 700, 1040];
    const posi = [
        [50, 50],
        [50, 360],
        [50, 700],
        [50, 1040],
        [380, 50],
        [380, 360],
        [380, 700],
        [380, 1040],
        [730, 50],
        [730, 360],
        [730, 700],
        [730, 1040],
        [1080, 50],
        [1080, 360],
        [1080, 700],
        [1080, 1040],
        [1430, 50],
        [1430, 360],
        [1430, 700],
        [1430, 1040],
        [1780, 50],
        [1780, 360],
        [1780, 700],
        [1780, 1040],
        [2130, 50],
        [2130, 360],
        [2130, 700],
        [2130, 1040]
    ];
    let originalArray = []; //原数组
    //给原数组originalArray赋值
    for (let i = 0; i < posi.length; i++) {
        originalArray[i] = i + 1;
    }
    originalArray.sort(function () {
        return 0.5 - Math.random();
    });
    for (let i = 0; i < imgs.length; i++) {
        let rot = getRandomArbitrary(-10, 10);
        let x, y;
        let now = posi[originalArray[i]];
        x = now[0] + getRandomArbitrary(-30, 30);
        y = now[1] + getRandomArbitrary(-20, 50);
        imgs[i].setAttribute("style",
            'transform:rotate(' + rot + 'deg);' + 'top:' + y + 'px;left:' + x + 'px;')
    }

    function getRandomArbitrary(min, max) {
        return Math.random() * (max - min) + min;
    }