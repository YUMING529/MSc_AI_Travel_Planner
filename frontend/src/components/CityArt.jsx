import React from 'react';
import compass from '../assets/compass.png';

export default function CityArt({small=false}) {
  return <img className={'city-art '+(small?'small':'')} src={compass} alt="Vintage compass printed on cream and golden paper"/>;
}
