import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CfaViewPage } from './cfa-view.page';

describe('CfaViewPage', () => {
  let component: CfaViewPage;
  let fixture: ComponentFixture<CfaViewPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(CfaViewPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
